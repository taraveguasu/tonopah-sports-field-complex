# CSI MasterFormat Divisions — Scope Assignment Reference

Used by `doc-indexer` to tag each package's `csi_divisions` and to map spec-manual-split filenames
(`div-XX-*.pdf`) to the right package(s). Only divisions actually present in a project's spec manual
need to be listed here — this is the Tonopah THS project's set (from
`00-source-docs/04-specs-reports/spec-manual-split/_manifest.json`); extend as needed for other projects.

| Division | Title | Typical package fit |
|---|---|---|
| 00 | Procurement & Contracting Requirements | Not package-specific — general conditions, bid forms |
| 01 | General Requirements | Applies to all packages (temp facilities, submittals, closeout) |
| 02 | Existing Conditions | Demolition packages |
| 03 | Concrete | Concrete package |
| 04 | Masonry | Masonry package |
| 05 | Metals | Structural steel & ornamental metals package |
| 06 | Wood, Plastics & Composites | FRP paneling — often folded into framing/drywall package |
| 07 | Thermal & Moisture Protection | Roofing package; moisture protection/sealants (non-1%) |
| 08 | Openings | Doors/frames/hardware, special doors (non-1%) |
| 09 | Finishes | Framing/drywall/painting package; acoustical ceilings, flooring (non-1%) |
| 10 | Specialties | Building/fire protection specialties, signage, lockers, flagpoles (non-1%) |
| 11 | Equipment | Food service equipment, scoreboards (non-1%) |
| 12 | Furnishings | Site furnishings (non-1%) |
| 13 | Special Construction | Shade structures — check package assignment, may be its own line item |
| 22 | Plumbing | Plumbing Systems package |
| 23 | HVAC | HVAC & Building Control Systems package |
| 26 | Electrical | Electrical & Low Voltage Systems package |
| 27 | Communications | Low-voltage/comms — usually folded into Electrical package |
| 31 | Earthwork | Site demo/earthwork package |
| 32 | Exterior Improvements | Asphalt paving, synthetic turf, running track, fencing, irrigation, landscaping — spans several packages, disambiguate by section number |
| 33 | Utilities | Wet utilities — part of site demo/earthwork/utilities package |

## Known ambiguity in Division 32 (Exterior Improvements)

This division bundles several distinct 1% packages by section number — do not assign the whole division
to one package:

| Section | Title | Package |
|---|---|---|
| 32 12 16 | Asphalt Paving | Site Demo/Earthwork package |
| 32 13 13 / 32 13 73 | Concrete Paving / Joint Sealants | Concrete package (or site package — confirm) |
| 32 16 23 | Sidewalks | Concrete package (or site package — confirm) |
| 32 18 13 | Synthetic Turf | Synthetic Turf Sports Field package |
| 32 18 23.33 | Running Track Surfacing | Running Track Surfacing package |
| 32 31 13 | Chain Link Fences and Gates | Fencing & Gates package |
| 32 84 00 | Landscape Irrigation | Landscaping & Irrigation package |
| 32 91 13 | Shot Put and Discus Mix | Track & Field Athletic Equipment (non-1%) or Running Track package — confirm |
| 32 96 50 | Invasive Plant Removal | Site Demo/Earthwork package |
