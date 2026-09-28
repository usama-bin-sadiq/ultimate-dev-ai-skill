# deepTools quick reference

One page of the commands used most often, the numbers you need to paste, and the
four rules that decide whether a result is interpretable. For per-tool options see
`references/tools_reference.md`; for full pipelines see `references/workflows.md`.

> **Provenance.** Authored from the descriptions in this skill's `SKILL.md` and
> reference files; no original copy of this quick reference was recovered, so
> treat the command flags as "verify against `deeptools --help` before you paste
> them" and the interpretive rules as the substance.

## The four rules

1. **Normalize before comparing.** Raw counts are not comparable across samples.
2. **Extend reads for ChIP-seq, never for RNA-seq.** Extension spans splice
   junctions and paints introns the transcript never contained.
3. **QC first.** `plotFingerprint` before anything else. If ChIP and input curves
   lie on top of each other, nothing downstream will mean anything.
4. **Same genome build for BAM and BED.** A mismatch produces empty or nonsense
   regions rather than an error.

## Normalization at a glance

| Method | Use for | Needs |
|---|---|---|
| `RPGC` | ChIP-seq and ATAC-seq coverage | `--effectiveGenomeSize` |
| `CPM` | RNA-seq bins, any cross-sample comparison | nothing |
| `RPKM` | RNA-seq gene bodies (length-corrected) | nothing |
| `BPM` | Binned signal, TPM-style scaling | nothing |
| `None` | Raw counts. Not for comparisons. | — |

```bash
# ChIP-seq, 1x genome coverage
bamCoverage --bamFile ChIP.bam -o chip.bw --normalizeUsing RPGC \
  --effectiveGenomeSize 2913022398 --extendReads --numberOfProcessors 8

# RNA-seq bins, strand-aware
bamCoverage --bamFile rna.bam -o rna_fwd.bw --normalizeUsing CPM \
  --binSize 10 --filterRNAstrand forward --extendReads 0
```

## Effective genome sizes (for RPGC)

| Organism | Assembly | Size |
|---|---|---|
| Human | GRCh38 / hg38 | `2913022398` |
| Human | GRCh37 / hg19 | `2864785220` |
| Human | T2T / CHM13CAT_v2 | `3117292070` |
| Mouse | GRCm39 / mm39 | `2654621783` |
| Mouse | GRCm38 / mm10 | `2652783500` |
| Zebrafish | GRCz11 | `1368780147` |
| *Drosophila* | dm6 | `142573017` |
| *C. elegans* | WBcel235 / ce11 | `100286401` |
| *C. elegans* | ce10 | `100258171` |
| *Arabidopsis* | TAIR10 | `119482012` |

Read-length-specific values for filtered human and mouse reads are in
`references/effective_genome_sizes.md`. A value that is wrong for your read length
under-normalises the top of the range and shows up as a compressed histogram.

## ChIP-seq

```bash
# 1. Fingerprint — ChIP against input, separately
bamFingerprint --bamfile ChIP.bam  --outFileName chip_fp.png  \
  --outQualityMetrics chip_fp.tab --numberOfProcessors 8 --skipZeros
bamFingerprint --bamfile Input.bam --outFileName input_fp.png \
  --outQualityMetrics input_fp.tab --numberOfProcessors 8 --skipZeros

# 2. Coverage distribution
plotCoverage --bamfile ChIP.bam --outFileName cov.png --numberOfProcessors 8

# 3. Fragment size, single-end only
bamPEFragmentSize --bamfile ChIP.bam --histogram frag.png --table frag.tab \
  --maxFragmentLength 1000

# 4. Filter, then normalise
alignmentSieve --bamFile ChIP.bam --outFileName chip_filt.bam \
  --extendReads --ignoreDuplicates --numberOfProcessors 8
bamCoverage --bamFile chip_filt.bam -o chip_rpgc.bw --binSize 50 \
  --normalizeUsing RPGC --effectiveGenomeSize 2913022398 --extendReads

# 5. ChIP over input
bamCompare --bamfile1 chip_rpgc.bw --bamfile2 input_rpgc.bw \
  --outFileName chip_vs_input.bw --operation log2 \
  --scaleFactorsMethod readCount --skipNonCoveredRegions
```

## Heatmaps and profiles

`computeMatrix` then `plotHeatmap` or `plotProfile` — always two steps.

```bash
# Around a reference point (TSS)
computeMatrix reference-point --scoreFileName chip.bw --regionsFileName genes.bed \
  --beforeRegionStartLength 3000 --afterRegionStartLength 3000 --binSize 50 \
  --missingDataAsZero -o matrix.tsv

# Scaled to each region (peak ranking, or gene body)
computeMatrix scale-regions --scoreFileName chip.bw --regionsFileName peaks.bed \
  --beforeRegionStartLength 3000 --afterRegionStartLength 3000 --binSize 50 \
  --missingDataAsZero -o matrix.tsv

plotHeatmap --colorMap RdBu --whatToShow "heatmap and colorbar" \
  --samplesLabel "ChIP" -o heatmap.png matrix.tsv

plotProfile --perGroup --colors "#1f78b4" -yAxisLabel "RPGC signal" \
  -o profile.png matrix.tsv
```

## Comparing more than two samples

```bash
multiBamSummary bins --bamfiles chip1.bw chip2.bw input.bw \
  --labels "ChIP 1" "ChIP 2" "Input" -o counts.tab -p 8

multiBigwigSummary BED-file --bwfiles chip1.bw chip2.bw \
  --bedFile peaks.bed --outFileName peaks.tab

plotCorrelation --correlateSpearman --whatToPlot heatmap --plotNumbers \
  -o corr.png counts.tab

plotPCA -o pca.png counts.tab
```

## Peak-centred enrichment

```bash
plotEnrichment --color "#1f78b4" -o enrichment.png \
  --BEDFile peaks.bed --labels "Peaks" --regionLength 2000 matrix.tsv
```

## ATAC-seq

```bash
# Tn5 correction: --ATACshift is --shift 4 -5 5 -4 on properly paired fragments
alignmentSieve --bamFile atac.bam --outFileName atac_filt.bam \
  --ATACshift --minFragmentLength 30 --maxFragmentLength 2000

bamCoverage --bamFile atac_filt.bam -o atac.bw --binSize 50 \
  --normalizeUsing RPGC --effectiveGenomeSize 2913022398

# Nucleosome ladder check, paired-end
bamPEFragmentSize --bamfile atac_filt.bam --histogram nuc.png \
  --table nuc.tab --maxFragmentLength 1000
```

A healthy library shows a sub-nucleosomal peak around 40-80 bp, a mononucleosome
peak near 150 bp, and a diminishing sub-nucleosome peak above it.

## GC bias

```bash
computeGCBias --bamfile ChIP.bam --genome genome.fa --effectiveGenomeSize 2913022398 \
  --GCbiasFrequenciesFile gc.txt --numberOfProcessors 8 --plotFile gc.png
correctGCBias gc.txt ChIP.bam corrected.bam
```

Apply it only when `computeGCBias` shows real bias, and never combine it with
`--ignoreDuplicates`: correctGCBias needs duplicate positions intact, and removing
them afterwards re-introduces the bias it was asked to remove.

## Parameters that appear everywhere

| Flag | Note |
|---|---|
| `--numberOfProcessors, -p` | Use the cores you have. `max` and `max/2` both work, and recent releases respect CPU affinity more carefully. |
| `--region` | `chr1:1-10000000` for parameter testing. Also the fix for out-of-memory. |
| `--binSize` | Bigger is faster and gives smaller files. |
| `--ignoreDuplicates` | Recommended for most ChIP-seq analyses. |
| `--minMappingQuality` | e.g. `10` to drop low-confidence alignments. |
| `--extendReads` | ChIP-seq: yes. RNA-seq: no. |
| `--centerReads` | Sharpens signal; useful for narrow peaks. |
| `--minFragmentLength` / `--maxFragmentLength` | Fragment bounds, especially for ATAC-seq. |
| `--samFlagInclude` / `--samFlagExclude` | SAM flag filtering. |

## When something goes wrong

| Symptom | Cause and fix |
|---|---|
| `BAM index not found` | `samtools index input.bam` |
| Killed, out of memory | `--region chr1`, or process one chromosome at a time |
| Slow | Raise `--numberOfProcessors`, raise `--binSize`, pre-filter with `alignmentSieve` |
| bigWig is enormous | `--binSize 50` or larger |
| Empty heatmap | BAM and BED on different builds, or the regions are outside the BAM's references |
| Signal halved in one strand | Wrong `--filterRNAstrand`, or the wrong STAR column upstream |
| Fingerprint curves overlap | No enrichment. Stop and fix the experiment, not the parameters |

## Before you run anything

```bash
python scripts/validate_files.py --bam sample1.bam sample2.bam --bed regions.bed

python scripts/workflow_generator.py --list
python scripts/workflow_generator.py chipseq_qc -o qc.sh \
  --input-bam Input.bam --chip-bams "ChIP1.bam ChIP2.bam" \
  --genome-size 2913022398 --threads 8
```

Installation: `uv pip install deepTools==3.5.6`, or
`conda install -c conda-forge -c bioconda deeptools` on a shared system.
