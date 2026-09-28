---
name: share-point-automation
description: "SharePoint Automation: manage sites, lists, documents, folders, pages, and search content across SharePoint and OneDrive"
requires:
  mcp: [rube]
---

# SharePoint Automation

Automate SharePoint operations including managing sites, lists, documents, folders, and pages. Integrates with both SharePoint REST API and Microsoft Graph via OneDrive.

**Toolkit docs:** [composio.dev/toolkits/share_point](https://composio.dev/toolkits/share_point)

---

## Setup

This skill requires the **Rube MCP server** connected at `https://rube.app/mcp`.

Before executing any tools, ensure active connections exist for the `share_point` and `one_drive` toolkits. If no connection is active, initiate one via `RUBE_MANAGE_CONNECTIONS`.

> **Note:** Many OneDrive/SharePoint tools only work with organizational Microsoft 365 accounts (Azure AD/Entra ID). Personal Microsoft accounts are NOT supported.

---

## Core Workflows

### 1. List and Browse Sites

Retrieve site details and enumerate subsites to discover the SharePoint topology.

**Tools:**
- `ONE_DRIVE_GET_SITE_DETAILS` -- Get metadata for a specific site by ID
- `ONE_DRIVE_LIST_SITE_SUBSITES` -- List all subsites of a parent site

**Key Parameters:**
- `site_id` (required) -- Composite format: `hostname,site-collection-guid,web-guid` (e.g., `"contoso.sharepoint.com,da60e844-...,712a596e-..."`)

**Example:**
```
Tool: ONE_DRIVE_GET_SITE_DETAILS
Arguments:
  site_id: "contoso.sharepoint.com,2C712604-1370-44E7-A1F5-426573FDA80A,2D2244C3-251A-49EA-93A8-39E1C3A060FE"
```

---

### 2. Manage Lists

Create lists, enumerate existing lists, and retrieve list items.

**Tools:**
- `SHARE_POINT_LIST_ALL_LISTS` -- Retrieve all lists on a site (supports OData filter, select, orderby, top)
- `SHARE_POINT_SHAREPOINT_CREATE_LIST` -- Create a new list with a specified template
- `ONE_DRIVE_LIST_SITE_LISTS` -- List all lists under a site via Microsoft Graph
- `ONE_DRIVE_GET_SHAREPOINT_LIST_ITEMS` -- Retrieve items from a specific list

**Key Parameters for `SHARE_POINT_SHAREPOINT_CREATE_LIST`:**
- `name` (required) -- List name
- `template` (required) -- Template type: `"genericList"`, `"documentLibrary"`, `"tasks"`, etc.
- `description` -- Optional description

**Key Parameters for `SHARE_POINT_LIST_ALL_LISTS`:**
- `filter` -- OData filter, e.g., `"Hidden eq false"`
- `select` -- Properties to return, e.g., `"Title,Id"`
- `orderby` -- Sort expression, e.g., `"Title desc"`
- `top` -- Limit results count

**Example:**
```
Tool: SHARE_POINT_SHAREPOINT_CREATE_LIST
Arguments:
  name: "Project Tasks"
  template: "tasks"
  description: "Task tracking for Q1 deliverables"
```

---

### 3. Manage Folders and Files

Create folders, list files within folders, and navigate the document library.

**Tools:**
- `SHARE_POINT_SHAREPOINT_CREATE_FOLDER` -- Create a new folder in a document library
- `SHARE_POINT_LIST_FILES_IN_FOLDER` -- List files within a folder by server-relative URL
- `SHARE_POINT_GET_FOLDER_BY_SERVER_RELATIVE_URL` -- Get folder metadata by path

**Key Parameters for `SHARE_POINT_SHAREPOINT_CREATE_FOLDER`:**
- `folder_name` (required) -- Name of the folder to create
- `document_library` -- Target library (default: `"Shared Documents"`)
- `relative_path` -- Additional path within the library

**Key Parameters for `SHARE_POINT_LIST_FILES_IN_FOLDER`:**
- `folder_name` (required) -- Server-relative URL, e.g., `"/Shared Documents"`
- `select` -- Comma-separated properties, e.g., `"Name,ServerRelativeUrl,Length"`
- `top` -- Limit results count
- `orderby` -- Sort expression, e.g., `"Name desc"`

**Example:**
```
Tool: SHARE_POINT_LIST_FILES_IN_FOLDER
Arguments:
  folder_name: "/Shared Documents/Reports"
  select: "Name,ServerRelativeUrl,Length"
  top: 50
```

---

### 4. Search SharePoint Content

Use Keyword Query Language (KQL) to search documents, list items, and other content across the site.

**Tool:** `SHARE_POINT_SEARCH_QUERY`

**Key Parameters:**
- `querytext` (required) -- KQL query, e.g., `"project report"`, `"FileType:docx"`, `"Author:\"John Doe\""`
- `rowlimit` -- Max results per request (default ~50, max 500)
- `startrow` -- Zero-based offset for pagination
- `selectproperties` -- Properties to return, e.g., `"Title,Author,Path"`
- `refinementfilters` -- Narrow results, e.g., `"FileType:equals(\"docx\")"`

**Example:**
```
Tool: SHARE_POINT_SEARCH_QUERY
Arguments:
  querytext: "IsDocument:1 FileType:pdf"
  rowlimit: 25
  selectproperties: "Title,Author,Path,LastModifiedTime"
```

---

### 5. Track List Changes (Delta Query)

Use delta queries to get incremental changes (created, updated, deleted items) without reading the entire list.

**Tool:** `ONE_DRIVE_LIST_SHAREPOINT_LIST_ITEMS_DELTA`

**Key Parameters:**
- `site_id` (required) -- Composite site ID
- `list_id` (required) -- List GUID
- `token` -- Omit for initial sync; pass `"latest"` for empty response with token; pass previous token for changes since
- `expand` -- e.g., `"fields($select=ColumnA,ColumnB)"`
- `top` -- Max items per response

---

### 6. Retrieve Site Page Content

Read modern SharePoint Site Pages content including canvas web parts.

**Tool:** `SHARE_POINT_GET_SITE_PAGE_CONTENT`

**Key Parameters:**
- `page_file_name` -- File name with `.aspx` extension, e.g., `"Home.aspx"`
- `item_id` -- Alternative: list item ID of the page
- `render_as` -- `"raw"` (default), `"text"`, or `"html"`
- `site` -- Optional site name scope

---

## Known Pitfalls

| Pitfall | Detail |
|---------|--------|
| **Site ID format** | Must be composite: `hostname,site-collection-guid,web-guid`. Incorrect format causes 400 errors. |
| **Personal accounts unsupported** | `ONE_DRIVE_LIST_SITE_LISTS` and Graph-based tools only work with organizational M365 accounts, not personal MSA/Outlook.com accounts. |
| **OData filter syntax** | SharePoint OData filters use specific syntax. Test filters incrementally; unsupported expressions may silently return empty results. |
| **Pagination** | Use `skiptoken` for server-side paging in list operations. Incomplete pagination settings can miss results. |
| **Folder paths** | Must use server-relative URLs (e.g., `/Shared Documents`) not absolute URLs. |

---

## Quick Reference

| Tool Slug | Description |
|-----------|-------------|
| `ONE_DRIVE_GET_SITE_DETAILS` | Get metadata for a SharePoint site |
| `ONE_DRIVE_LIST_SITE_SUBSITES` | List subsites of a parent site |
| `ONE_DRIVE_LIST_SITE_LISTS` | List all lists under a site (Graph API) |
| `ONE_DRIVE_LIST_SHAREPOINT_LIST_ITEMS_DELTA` | Track incremental list changes |
| `ONE_DRIVE_GET_SHAREPOINT_LIST_ITEMS` | Retrieve items from a list |
| `ONE_DRIVE_LIST_DRIVES` | List available drives for a user/site/group |
| `ONE_DRIVE_LIST_SITE_COLUMNS` | List column definitions for a site |
| `SHARE_POINT_LIST_ALL_LISTS` | Retrieve all lists on a site (REST API) |
| `SHARE_POINT_SHAREPOINT_CREATE_LIST` | Create a new SharePoint list |
| `SHARE_POINT_SHAREPOINT_CREATE_FOLDER` | Create a folder in a document library |
| `SHARE_POINT_LIST_FILES_IN_FOLDER` | List files in a folder |
| `SHARE_POINT_SEARCH_QUERY` | Search content using KQL |
| `SHARE_POINT_GET_SITE_PAGE_CONTENT` | Retrieve Site Page content |
| `SHARE_POINT_GET_FOLDER_BY_SERVER_RELATIVE_URL` | Get folder metadata by path |

---

*Powered by [Composio](https://composio.dev)*

## Prerequisites

<!-- Carried from the underscore-named share_point-automation skill,
     which this one replaces. Generic Composio working knowledge,
     product-independent. -->

- Rube MCP must be connected (RUBE_SEARCH_TOOLS available)
- Active SharePoint connection via `RUBE_MANAGE_CONNECTIONS` with toolkit `share_point`
- Always call `RUBE_SEARCH_TOOLS` first to get current tool schemas

## Tool Discovery

<!-- Carried from the underscore-named share_point-automation skill,
     which this one replaces. Generic Composio working knowledge,
     product-independent. -->

Always discover available tools before executing workflows:

```
RUBE_SEARCH_TOOLS: queries=[{"use_case": "document libraries, sites, lists, and content management", "known_fields": ""}]
```

This returns:
- Available tool slugs for SharePoint
- Recommended execution plan steps
- Known pitfalls and edge cases
- Input schemas for each tool

## Search Before Action

<!-- Carried from the underscore-named share_point-automation skill,
     which this one replaces. Generic Composio working knowledge,
     product-independent. -->

Always search for existing resources before creating new ones to avoid duplicates.

## Pagination

<!-- Carried from the underscore-named share_point-automation skill,
     which this one replaces. Generic Composio working knowledge,
     product-independent. -->

Many list operations support pagination. Check responses for `next_cursor` or `page_token` and continue fetching until exhausted.

## Error Handling

<!-- Carried from the underscore-named share_point-automation skill,
     which this one replaces. Generic Composio working knowledge,
     product-independent. -->

- Check tool responses for errors before proceeding
- If a tool fails, verify the connection is still ACTIVE
- Re-authenticate via `RUBE_MANAGE_CONNECTIONS` if connection expired

## Batch Operations

<!-- Carried from the underscore-named share_point-automation skill,
     which this one replaces. Generic Composio working knowledge,
     product-independent. -->

For bulk operations, use `RUBE_REMOTE_WORKBENCH` with `run_composio_tool()` in a loop with `ThreadPoolExecutor` for parallel execution.

## Common Patterns

<!-- Carried from the underscore-named share_point-automation skill,
     which this one replaces. Generic Composio working knowledge,
     product-independent. -->

