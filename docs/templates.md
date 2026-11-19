# AAOF template provenance

Reference: *Scaled Measurements from the AAOF Legacy Collection Images*, v1.9, 2022-02-28.
`data/templates.json` records the exact SHA256 of the supplied PDF. Page numbers below are
1-based PDF pages including the cover; printed page numbers are one lower. Original
millimetre coordinates are stored in **A,B,C,D** order without rounding or normalization.
The matcher reflects the Cartesian y axis only when comparing with image-array coordinates.

| ID | Collection / scope | PDF pages | Special handling |
|---|---|---|---|
| `iowa` | Iowa Growth | 4 | Near-symmetry can make names ambiguous. |
| `mathews` | Mathews Growth | 4 | The PDF flags one website identification error. |
| `forsyth_twin_original` | Original pinpoint Forsyth Twin films | 5 | Not the inconsistent 90 subjects added in 2018. |
| `fels` | Fels Longitudinal | 5 | Identical coordinates to original Forsyth and ordinary Oregon. |
| `denver` | Denver Growth | 5–6 | D=(228.4,7.3) is continued at the top of PDF page 6. |
| `michigan` | Michigan Growth | 6 | Use outer four corners when five marks per side are present. |
| `oregon_optical` | Nine early optical-pattern Oregon subjects | 6 | Optical circle/cross appearance remains experimentally supported. |
| `oregon` | Remaining Oregon Growth subjects | 6 | Identical to original Forsyth/Fels. |
| `burlington` | Burlington Growth | 7 | Older deliveries can have different DPI; pre-v1.2 tables were corrected. |
| `bolton_brush` | Bolton-Brush Growth | 7–8 | Supports reversed punch-template placement. |

The two standard/reversed Bolton-Brush right-side distances are approximately 159.6 and
152.5 mm. Those refer to the PDF's illustrated orientations. An arbitrarily rotated input
must first be matched to a physical label assignment; its screen-right edge is not assumed
to be CD. Anatomical skull orientation is a separate question and is not inferred.

Nominal scan DPI is metadata, not a universal pixel-to-mm assumption. Images can have been
resized or scanned anisotropically. Compatible dimensionless geometry does not establish
identical physical dimensions, collection identity or a clinically valid scale.

Richardson has no coordinate table in this document. Likewise, no single consistent table
is supplied for the later Forsyth cohort. Such input can still return compatible geometries
as tentative hypotheses, but this library does not invent a `richardson`/later-Forsyth template
or claim that its data provenance has been identified.
