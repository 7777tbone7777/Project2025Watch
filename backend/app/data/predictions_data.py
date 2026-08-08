"""Real Project 2025 proposals, replacing the numbered placeholder scaffolding.

The previous list was template stubs — "Executive Order 1: Streamline Federal
Bureaucracy", "Judicial Appointment 1: Conservative Judge" — with no relationship
to the actual Mandate for Leadership. Scoring those correctly still tells you
nothing, so the content is rebuilt from the document and from published trackers.

Each entry carries:
  agency    - the department/agency it concerns, so results can be grouped
  keywords  - a NewsAPI query. Syntax matters: "quoted phrase" AND (alt OR alt).
              A bare space-separated string returns ZERO results, which is what
              the old code sent (it searched the prediction sentence verbatim).
              Every query here was checked against the live API for >0 matches.
  source    - where the proposal is documented, so any status is checkable

Editorial stance: these are recorded as PROPOSALS and matched against reported
events. Whether each is desirable is not this file's business — the tracker is
useful precisely because someone who disagrees with its author can still check it.
"""

# timeframe values are the window a proposal was expected/observed to move in.
PREDICTIONS = [
    # ---------------- civil service / personnel ----------------
    {
        "timeframe": "Jan-Mar 2025",
        "prediction": "Reinstate Schedule F, reclassifying career civil servants in policy roles "
                      "to strip removal protections",
        "agency": "Office of Personnel Management",
        "keywords": "(\"Schedule F\" OR \"Schedule Policy/Career\") AND (federal OR \"civil service\" OR OPM)",
        "source": "Mandate for Leadership ch.3 (Central Personnel Agencies); EO 13957 lineage",
    },
    {
        "timeframe": "Jan-Mar 2026",
        "prediction": "Finalize the Schedule Policy/Career rule and convert career positions into it",
        "agency": "Office of Personnel Management",
        "keywords": "(\"Schedule Policy/Career\" OR \"Schedule F\") AND (rule OR OPM OR convert)",
        "source": "OPM final rule, Feb 2026; EO June 2026 converting ~10,000 positions",
    },
    {
        "timeframe": "Apr-Jun 2025",
        "prediction": "Weaken federal employee unions by curtailing collective bargaining rights",
        "agency": "Office of Personnel Management",
        "keywords": "\"collective bargaining\" AND (federal AND (union OR employees))",
        "source": "project2025.observer — recorded completed 24 Apr 2026, partially enjoined 15 May",
    },
    {
        "timeframe": "Jan-Mar 2025",
        "prediction": "Impose a federal hiring freeze and a government-wide regulatory freeze",
        "agency": "Executive Office of the President",
        "keywords": "(\"hiring freeze\" OR \"regulatory freeze\") AND federal",
        "source": "Mandate for Leadership ch.1 (White House Office)",
    },

    # ---------------- education ----------------
    {
        "timeframe": "Jan-Mar 2025",
        "prediction": "Eliminate the federal Department of Education, moving or dismantling its programs",
        "agency": "Department of Education",
        "keywords": "\"Department of Education\" AND (dismantle OR abolish OR eliminate)",
        "source": "Mandate for Leadership ch.11, pp.319-361 (Lindsey M. Burke)",
    },
    {
        "timeframe": "Apr-Jun 2025",
        "prediction": "Eliminate or phase out Title I funding for low-income schools",
        "agency": "Department of Education",
        "keywords": "\"Title I\" AND (funding OR schools OR eliminate)",
        "source": "Mandate for Leadership ch.11",
    },
    {
        "timeframe": "Jul-Sep 2025",
        "prediction": "Expand school choice through vouchers and tuition tax credits",
        "agency": "Department of Education",
        "keywords": "(\"school choice\" OR vouchers) AND (\"tax credit\" OR federal OR private)",
        "source": "Mandate for Leadership ch.11",
    },
    {
        "timeframe": "Oct-Dec 2025",
        "prediction": "End income-driven student loan repayment programs",
        "agency": "Department of Education",
        "keywords": "(\"income-driven repayment\" OR \"student loan\") AND (repayment OR forgiveness)",
        "source": "Mandate for Leadership ch.11",
    },

    # ---------------- justice / law enforcement ----------------
    {
        "timeframe": "Jan-Mar 2025",
        "prediction": "Expand the number of political appointees throughout the Department of Justice",
        "agency": "Department of Justice",
        "keywords": "\"Justice Department\" AND (\"political appointees\" OR prosecutors)",
        "source": "Mandate for Leadership ch.17 (Department of Justice)",
    },
    {
        "timeframe": "Apr-Jun 2025",
        "prediction": "Review major FBI investigations for conformity with the President's agenda",
        "agency": "Federal Bureau of Investigation",
        "keywords": "FBI AND (investigations AND (political OR independence OR \"White House\"))",
        "source": "Mandate for Leadership ch.17; Brennan Center analysis",
    },
    {
        "timeframe": "Apr-Jun 2025",
        "prediction": "Relax restrictions on White House communication with DOJ about active investigations",
        "agency": "Department of Justice",
        "keywords": "\"Justice Department\" AND (\"White House\" AND (contacts OR independence))",
        "source": "Mandate for Leadership ch.17",
    },

    # ---------------- energy / environment ----------------
    {
        "timeframe": "Jan-Mar 2026",
        "prediction": "Rescind or replace the EPA's 2009 greenhouse gas endangerment finding",
        "agency": "Environmental Protection Agency",
        "keywords": "\"endangerment finding\" AND (EPA OR rescind OR greenhouse)",
        "source": "project2025.observer — recorded completed 12 Feb 2026",
    },
    {
        "timeframe": "Jan-Mar 2026",
        "prediction": "Eliminate carbon capture, utilization and storage programs",
        "agency": "Department of Energy",
        "keywords": "\"carbon capture\" AND (grants OR canceled OR program)",
        "source": "project2025.observer — recorded completed 15 Jan 2026, 24 grants canceled",
    },
    {
        "timeframe": "Jul-Sep 2026",
        "prediction": "Narrow the Endangered Species Act definition of critical habitat",
        "agency": "Department of the Interior",
        "keywords": "\"Endangered Species Act\" AND (\"critical habitat\" OR rule)",
        "source": "project2025.observer — recorded completed 10 Jul 2026",
    },

    # ---------------- health / HHS ----------------
    {
        "timeframe": "Jan-Mar 2026",
        "prediction": "End or restrict federal funding for fetal stem cell research",
        "agency": "National Institutes of Health",
        "keywords": "(\"fetal tissue\" OR \"stem cell\") AND (NIH OR research OR funding)",
        "source": "project2025.observer — recorded completed 22 Jan 2026",
    },
    {
        "timeframe": "Jan-Mar 2026",
        "prediction": "Rescind Office of Refugee Resettlement policy providing abortion access to "
                      "unaccompanied pregnant minors",
        "agency": "Department of Health and Human Services",
        "keywords": "\"Refugee Resettlement\" AND (abortion OR minors OR policy)",
        "source": "project2025.observer — recorded completed 1 Mar 2026",
    },
    {
        "timeframe": "Apr-Jun 2026",
        "prediction": "Restore the Conscience and Religious Freedom Division within HHS civil rights",
        "agency": "Department of Health and Human Services",
        "keywords": "(\"religious freedom\" AND (HHS OR \"civil rights\" OR conscience))",
        "source": "project2025.observer — recorded completed 30 Jun 2026",
    },
    {
        "timeframe": "Jul-Sep 2026",
        "prediction": "Restrict Teen Pregnancy Prevention Program grants to abstinence-centred programs",
        "agency": "Department of Health and Human Services",
        "keywords": "(\"teen pregnancy\" OR abstinence) AND (grants OR program OR funding)",
        "source": "project2025.observer — recorded completed 22 Jul 2026, 53 of 67 grants canceled",
    },

    # ---------------- defense / foreign policy ----------------
    {
        "timeframe": "Apr-Jun 2026",
        "prediction": "Reduce US force posture in Europe",
        "agency": "Department of Defense",
        "keywords": "(NATO OR \"US troops\") AND (Europe AND (withdrawal OR posture OR reduce))",
        "source": "project2025.observer — recorded completed 1 May 2026",
    },

    # ---------------- media ----------------
    {
        "timeframe": "Apr-Jun 2025",
        "prediction": "Eliminate federal funding for public broadcasting (CPB)",
        "agency": "Corporation for Public Broadcasting",
        "keywords": "(\"public broadcasting\" OR NPR OR PBS) AND (funding OR defund)",
        "source": "Mandate for Leadership ch.8 (Media Agencies)",
    },

    # ---------------- spending control ----------------
    {
        "timeframe": "Jan-Mar 2025",
        "prediction": "Give political appointees authority to review and authorise appropriated funding",
        "agency": "Office of Management and Budget",
        "keywords": "(OMB OR \"Office of Management and Budget\") AND (apportionment OR funding OR impoundment)",
        "source": "Mandate for Leadership ch.2 (Office of Management and Budget)",
    },
]


_QUARTER_ORDER = {"Jan-Mar": 0, "Apr-Jun": 1, "Jul-Sep": 2, "Oct-Dec": 3}


def _timeframe_key(timeframe: str):
    """Sort 'Apr-Jun 2025' chronologically, not alphabetically.

    Alphabetical ordering interleaves years — 'Apr-Jun 2026' sorts before
    'Jan-Mar 2025' — which makes the timeline read as nonsense.
    """
    try:
        quarter, year = timeframe.rsplit(" ", 1)
        return (int(year), _QUARTER_ORDER.get(quarter, 9))
    except Exception:
        return (9999, 9)


# Keep the list itself in chronological order so every consumer inherits it.
PREDICTIONS.sort(key=lambda p: _timeframe_key(p["timeframe"]))


def timeframes():
    """Distinct timeframes, chronological."""
    seen = []
    for p in PREDICTIONS:
        if p["timeframe"] not in seen:
            seen.append(p["timeframe"])
    return seen


def agencies():
    return sorted({p["agency"] for p in PREDICTIONS})
