---
name: museum-collection-api
description: Query museum collection APIs to retrieve object records, image URLs, and metadata for GHB research. Handles British Museum, Metropolitan Museum of Art, Rijksmuseum, and Art Institute of Chicago. Falls back to Archive.org for text sources. Use when researching art objects, iconography, or visual culture for the Global History of Erotic Art or related projects.
version: 1.0.0
author: Michael Fox / Claude Code
license: MIT
metadata:
  hermes:
    tags: [Research, Museums, GHB, API, Collections, Art-History, Iconography]
    related_skills: [scholarly-source-acquisition, browser-source, vault-cold-memory]
---

# Museum Collection API

Retrieves structured object records from major museum APIs without browser automation or Cloudflare risk. Use this skill before browser-source — it is faster, autonomous, and requires no Mike approval step.

## Source Priority

Always try in this order:

1. **Metropolitan Museum of Art** (`met`) — free, no auth, 400k+ objects, confirmed working. Strong Italian/Spanish coverage: 38 El Greco works, Titian, Raphael, Michelangelo, Veronese.
2. **Art Institute of Chicago** (`aic`) — free, no auth, confirmed working. Strong Impressionist (Monet, Renoir, Degas, Toulouse-Lautrec), also Italian masters.
3. **Wikimedia Commons** (`wikimedia`) — free, no auth, confirmed working. Best for named-artist searches: Botticelli, Raphael, El Greco, Michelangelo, Velázquez, Caravaggio. Full images for all public domain works.
4. **Rijksmuseum** (`rijks`) — free, Dutch Golden Age strength: Rembrandt, Vermeer, Hals. Century-based date filter.
5. **Louvre** (`louvre`) — French masters, classical sculpture. API endpoint may shift; script handles gracefully.
6. **Uffizi** (`uffizi`) — Botticelli, Leonardo, early Italian. Falls back to Europeana if direct API unavailable.
7. **British Museum** (`bm`) — prints, drawings, coins, antiquities. Cloudflare may block; script skips gracefully if so.
8. **Europeana** (`europeana`) — pan-European aggregator; fallback for sources not covered above.
9. **Archive.org** — text/catalog fallback for exhibition catalogs and art history publications.

## Constitutional Rule

Museum APIs are open-access research infrastructure. Use them fully and autonomously. Record image URLs and metadata — do not bulk-download image files unless Mike explicitly authorizes it. For GHB sourcing, record the museum URL, accession number, and BibTeX entry.

## Running the Tool

```bash
python ~/.hermes/skills/research/museum-collection-api/scripts/museum_search.py \
  --query "venus mythological nude" \
  --period "1400-1900" \
  --sources bm,met,rijks,aic \
  --output ~/ObsidianVault/07\ -\ Global\ History\ Book/References/museum_results.jsonl
```

Or interactively from Python:
```python
exec(open('/root/.hermes/skills/research/museum-collection-api/scripts/museum_search.py').read())
results = search_all("susannah bathing biblical", period=(1400, 1900))
for r in results[:10]:
    print(r['title'], '|', r['source'], '|', r['object_url'])
```

## Standard Workflow

1. Identify the research query — subject, period, medium (optional), subject category (Biblical / Mythological / Genre)
2. Run `museum_search.py` with appropriate parameters
3. Review results — flag objects with high-quality images for GHB illustration candidates
4. Write BibTeX records for cited works (use `--bibtex` flag or template below)
5. Append to `GHB_bibliography.bib`
6. Save full result set to cold memory if > 20 objects

## Subject Categories for GHB Research

Use these as `--tags` or query terms:

**Biblical subjects (legitimized nude)**
- Susannah and the Elders
- Bathsheba at Her Bath
- Judith and Holofernes
- The Fall of Man / Adam and Eve
- Mary Magdalene
- Salome
- The Virgin (Madonna — contrast with sensuality)

**Mythological subjects (classical legitimization)**
- Venus / Aphrodite (rising, sleeping, at her toilet)
- Diana / Artemis and Actaeon
- Leda and the Swan
- The Three Graces
- Danae
- Europa
- Nymphs and Satyrs
- Pygmalion

**Genre / Actual Humans (life study, studio practice)**
- Reclining female nude (odalisque)
- Artist's studio / model
- Bathers (baigneuses)
- Turkish bath / harem
- Life drawing / académie

**Transitional / Victorian moral anxiety**
- "Spirit" and "allegory" framing of nude
- Pre-Raphaelite idealization vs. realism
- Salon vs. Impressionist treatment of the body

## Period Reference

| Era | Approx. Dates | Key Context |
|---|---|---|
| Early Renaissance | 1400–1500 | Reintroduction of classical nude; religious framing dominant |
| High Renaissance | 1490–1560 | Titian, Raphael, Michelangelo; mythological nude matures |
| Mannerism | 1520–1600 | Elongation, self-consciousness; erotic tension |
| Baroque | 1600–1750 | Rubens, Rembrandt, Caravaggio; flesh and power |
| Neoclassical | 1750–1830 | Return to idealized classical nude; moral elevation rhetoric |
| Romanticism | 1800–1850 | Orientalism; the "other" as license for nudity |
| Realism | 1840–1880 | Courbet; the nude as actual body — scandal |
| Impressionism | 1860–1900 | Manet, Renoir, Degas; the modern body |
| Victorian (Britain) | 1837–1901 | Moral policing; obscenity law development |

## BibTeX Template for Museum Objects

```bibtex
@misc{ArtistYYYY,
  author       = {Artist Last, First},
  title        = {Object Title},
  year         = {YYYY},
  howpublished = {[Medium]. [Museum Name], [City]. Accession No. XXXXX},
  url          = {https://museum-url/object-page},
  note         = {GHB subject category: Biblical|Mythological|Genre. Image: [URL if available]. Retrieved via museum API YYYY-MM-DD.}
}
```

## API Reference

See `scripts/museum_search.py` for implementation. Key endpoints:

- Met: `https://collectionapi.metmuseum.org/public/collection/v1/search`
- AIC: `https://api.artic.edu/api/v1/artworks/search`
- Rijksmuseum: `https://www.rijksmuseum.nl/api/en/collection`
- Louvre: `https://collections.louvre.fr/en/api/search`
- BM collection: `https://www.britishmuseum.org/collection/search` (Cloudflare — may block; script handles gracefully)
- Europeana: `https://api.europeana.eu/record/v2/search.json`
- Archive.org: `https://archive.org/advancedsearch.php` (text/catalog fallback)

## Reporting

After each run, report:
- Total objects found per source
- Objects with images (illustration candidates)
- Objects without images (metadata-only, still citable)
- Any sources that were blocked or returned errors
- BibTeX records appended

If a source is blocked, note it and continue — do not stop the run.
