"""Parse the official NOAA CPC ENSO probability forecast.

The IRI plume (numeric Nino 3.4 model forecasts) stopped being published as data
in 2026 ("we are no longer providing forecast data"). The machine readable
official forecast that remains is the CPC ENSO probability table: for each of the
next overlapping 3 month seasons, the chance of La Nina, Neutral, or El Nino.

Crucially, CPC defines the phases exactly as we do: El Nino above +0.5 C and La
Nina below -0.5 C in the Nino 3.4 region, on the 1991 to 2020 base. So their phase
probabilities and ours are directly comparable, which is what step 4 needs.

The page is static HTML: an "Issued <Month Year>" heading and a table whose rows
are `SEASON  La Nina%  Neutral%  El Nino%`. This parses that. Pure and offline:
feed it the page text (a fixture, or a live download), it never touches the network.
"""
import re

_ISSUED = re.compile(r"<h2>\s*Issued\s+([^<]+?)\s*</h2>", re.IGNORECASE)
_ROW = re.compile(
    r"<abbr>\s*(\w+)\s*<span[^>]*>([^<]+)</span>\s*</abbr>\s*</th>"
    r"\s*<td>\s*(\d+)\s*</td>\s*<td>\s*(\d+)\s*</td>\s*<td>\s*(\d+)\s*</td>",
    re.IGNORECASE,
)


def parse_cpc_probabilities(html):
    """Return the issue label and the per season phase probabilities.

    {"issued": "August 2026",
     "seasons": [{"season": "JAS", "months": "Jul Aug Sep",
                  "p_la_nina": 0, "p_neutral": 0, "p_el_nino": 100}, ...]}
    Percentages are integers as published. Raises if the table is absent (the
    page format changed), which is the honest failure, not a silent empty.
    """
    issued_m = _ISSUED.search(html)
    seasons = []
    for m in _ROW.finditer(html):
        season, months, ln, neu, en = m.groups()
        seasons.append({
            "season": season,
            "months": months.strip(),
            "p_la_nina": int(ln),
            "p_neutral": int(neu),
            "p_el_nino": int(en),
        })
    if not seasons:
        raise ValueError("no CPC probability rows found (page format may have changed)")
    return {"issued": issued_m.group(1).strip() if issued_m else None, "seasons": seasons}
