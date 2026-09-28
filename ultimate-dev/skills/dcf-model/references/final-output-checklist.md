<!-- Moved verbatim from dcf-model/SKILL.md, the 'section' section. Relative links were rebased for the new depth; the prose is otherwise unchanged. -->

# Final Output Checklist

Before delivering DCF model:

**Required:**
- Run `python recalc.py model.xlsx 30` until status is "success" (zero formula errors)
- Two sheets: DCF (with sensitivity at bottom), WACC
- Font colors: Blue=inputs, Black=formulas, Green=sheet links
- Cell comments on ALL hardcoded inputs
- Sensitivity tables fully populated with formulas
- Professional borders around major sections

**Validation:**
- OpEx based on revenue (not gross profit)
- Terminal value 50-70% of EV
- Terminal growth < WACC
- Tax rate 21-28%
- File naming: `[Ticker]_DCF_Model_[Date].xlsx`
