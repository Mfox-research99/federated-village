---
name: scholarly-source-acquisition
description: Find, verify, log, and lawfully download scholarly books, articles, and public-domain or open-access PDFs for Minerva's research library. Use when Mike asks for Archive.org, Google Scholar, UC Press, JSTOR, Project MUSE, author PDF, or reference-library retrieval work.
tags: [research, source-retrieval, archive-org, google-scholar, open-access, reference-library, minerva]
---

# Scholarly Source Acquisition

Use this skill when asked to locate source materials, especially when the task says to search Archive.org, Google Scholar, publisher sites, university repositories, or author pages and report URLs/download status.

## Constitutional rule

Download only lawful files:
- Public domain scans are OK.
- Open-access PDFs and author-posted PDFs are OK.
- Publisher freebies are OK.
- Controlled Digital Lending, preview-only books, paywalled PDFs, shadow libraries, or bypassed access are not downloads. Record the URL and status instead.

Do not use pirated sources. Do not bypass paywalls, logins, DRM, lending restrictions, or institutional access.

## Standard workflow

## Autonomy rule

When Mike has already authorized source acquisition, do the retrieval work instead of asking him to babysit links.

Good behavior:
- keep searching until each item is `downloaded`, `open-no-download`, `controlled-lending`, `paywalled`, `metadata-only`, or `not-found`
- download lawful public-domain or open-access files when available
- record uncertain or blocked items and move on
- give a complete report at the end
- **For Archive.org materials found via API search:** Verify access type (public domain, lending, paywalled) using the API before reporting. Report the exact access status, not "check the page yourself."

Avoid:
- asking Mike to visit Archive.org links unless a human login, CAPTCHA, lending checkout, purchase, or other genuinely human-only step blocks progress
- offering "fast vs thorough" choices after the task has already been authorized
- stopping after finding metadata when a lawful file check is still possible
- suggesting Mike "choose an approach" when authorization has already been given; complete the authorized task autonomously

1. Identify the exact requested item:
   - author
   - title
   - edition/volume if relevant
   - desired file type
   - destination library folder

2. Search easiest lawful paths first:
   - Archive.org for public-domain or downloadable scans.
   - Google Scholar for author-hosted `[PDF]` copies.
   - Publisher page for explicit open/free PDF links.
   - University repository or author faculty page.
   - Library/lending page only as a lead, not as a direct download unless it provides a lawful public file.

3. For each candidate, record:
   - title found
   - author
   - URL
   - access status: `downloaded`, `open-no-download`, `controlled-lending`, `paywalled`, `metadata-only`, or `not-found`
   - file size if visible or measurable after download
   - notes about edition mismatch, missing volume, OCR quality, or legal uncertainty

4. Download only when status is clearly lawful.
   - Prefer PDF.
   - Preserve meaningful filenames: `Author_Year_Short_Title.pdf`.
   - If source gives a stable identifier, save it in `access_notes.txt`.

5. Update the project reference library:
   - Put files in the correct `References/` subfolder.
   - Create or update `access_notes.txt` beside the material.
   - Update `MANIFEST.md` or the relevant tracking note if it exists.

6. Write a BibTeX record for every source found — downloaded or not.
   - Append to the master bibliography file at:
     `~/ObsidianVault/07 - Global History Book/References/GHB_bibliography.bib`
   - Use the BibTeX template below.
   - Write a record for every item regardless of access status — even `paywalled` or `not-found` items belong in the bibliography as stubs so Mike can import and track them in Zotero.

7. Report in the user's requested format first, then add short notes.

## BibTeX output

After each acquisition run, append records to `GHB_bibliography.bib`. Use the appropriate entry type:

```bibtex
@book{AuthorYYYY,
  author    = {Last, First},
  title     = {Full Title: Including Subtitle},
  year      = {YYYY},
  publisher = {Publisher Name},
  address   = {City},
  isbn      = {ISBN if known},
  url       = {URL if open access},
  note      = {access: downloaded | open-no-download | controlled-lending | paywalled | not-found. File: Author_Year_Short_Title.pdf if downloaded.}
}

@article{AuthorYYYY,
  author  = {Last, First},
  title   = {Article Title},
  journal = {Journal Name},
  year    = {YYYY},
  volume  = {N},
  number  = {N},
  pages   = {NNN--NNN},
  doi     = {DOI if known},
  url     = {URL if open access},
  note    = {access: downloaded | paywalled | etc.}
}
```

Rules:
- BibTeX key format: `AuthorYYYY` (e.g. `Rich1980`, `Foucault1978`). Add `a/b` suffix if same author/year.
- Always fill `author`, `title`, `year`. Fill the rest from whatever metadata is available.
- The `note` field must always record access status and filename if downloaded.
- Do not overwrite existing entries — check the `.bib` file for duplicates before appending.
- If the `.bib` file does not exist yet, create it with a header comment:
  ```
  % GHB Reference Library — Global History of Erotic Art
  % Auto-generated by Minerva scholarly-source-acquisition skill
  % Import into Zotero: File > Import > BibTeX
  ```

## Report template

```text
Evans - Palace of Minos: Found - URL: <url> - Status: downloaded/open/etc. - Size: <if known>
Rich - Compulsory Heterosexuality: Found - URL: <url> - Status: downloaded/open/etc. - Size: <if known>
Foucault - History of Sexuality Vol. 1: Found - URL: <url> - Status: controlled-lending/open/etc. - Size: <if known>
Keuls - Reign of the Phallus: Not Found - URL: <best metadata URL if any> - Status: paywalled/metadata-only/etc.
```

## Minerva's GHB defaults

For the Global History of Erotic Art project, default destination:

```text
~/ObsidianVault/07 - Global History Book/References/
```

Suggested folders for the current Tier 1A retrieval set:
- Evans, `Palace of Minos`: `04_MINOAN_CRETE/`
- Rich, `Compulsory Heterosexuality`: `00_FOUNDATIONAL_THEORY/`
- Foucault, `History of Sexuality Vol. 1`: `00_FOUNDATIONAL_THEORY/`
- Keuls, `Reign of the Phallus`: `04_MINOAN_CRETE/`

If a file cannot be downloaded lawfully, save a short `access_notes.txt` entry with the URL and what blocked retrieval.

## Search hints

Archive.org:
```bash
# API search for exact title + author (most reliable)
curl -s "https://archive.org/advancedsearch.php?q=TITLE+AUTHOR&output=json&rows=10" | jq '.response.docs[] | {title, identifier, creator}'

# Specific identifier lookup
curl -s "https://archive.org/advancedsearch.php?q=identifier:IDENTIFIER&output=json" | jq '.response.docs[0]'
```

**Archive.org API method:** Search by title + author first (high precision), record identifier, then check access type by examining the returned record. Most public-domain and open-access materials will have clear indicators.

Google Scholar:
- Search exact title plus author.
- Look for right-column PDF links, university repositories, or author pages.
- Treat ResearchGate/Academia pages as leads unless a direct lawful PDF is accessible.

Publisher pages:
- Search title + publisher.
- Use open/free PDF links only when the page explicitly offers them.

## Current prompt pattern

When Mike gives a list like:

```text
Evans - Palace of Minos
Rich - Compulsory Heterosexuality
Foucault - History of Sexuality Vol. 1
Keuls - Reign of the Phallus
```

Run the workflow item by item, easiest first, and keep a running acquisition log so interrupted work can resume.

If interrupted or compacted, resume from the acquisition log rather than asking Mike to restate the task.
