"""
Alpine Analytics — Home / Overview
"""

import streamlit as st

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("# Alpine Analytics")
st.markdown("##### Insight · Performance · Elevation")
st.markdown("---")

# ── Navigation cards ──────────────────────────────────────────────────────────
c1, c2, c3 = st.columns(3, gap="large")

with c1:
    st.markdown("### Athlete Profile")
    st.markdown(
        "Search any athlete to explore their momentum trend, "
        "strokes gained, performance tier, and best courses."
    )
    st.page_link("pages/1_Athlete.py", label="Open Athlete Profile →")

with c2:
    st.markdown("### Race Results")
    st.markdown(
        "Browse any race — full field results, podium breakdown, "
        "over/underperformers, and field distribution charts."
    )
    st.page_link("pages/2_Race_Results.py", label="Open Race Results →")

with c3:
    st.markdown("### Course Explorer")
    st.markdown(
        "Explore venue difficulty, course setter analysis, hill difficulty index, "
        "best courses, and course similarity comparisons."
    )
    st.page_link("pages/3_Course_Explorer.py", label="Open Course Explorer →")

st.markdown("---")

# ── About ─────────────────────────────────────────────────────────────────────
st.markdown("## What is Alpine Analytics?")
st.markdown(
    """
Alpine Analytics applies data science to FIS alpine ski racing — going beyond podium positions
to answer deeper questions about **athlete performance**, **course difficulty**, and **race dynamics**.

Traditional race results tell you *where* an athlete finished, but not *how well* they performed
relative to the field. A 10th place in a 70-person World Cup field at Wengen tells a very different story
than 10th in a 30-person regional race. Alpine Analytics puts every result in context by measuring
performance against the actual competition on that day.
"""
)

st.markdown("---")

# ── Key concepts ──────────────────────────────────────────────────────────────
st.markdown("## Key Concepts Explained")

k1, k2 = st.columns(2, gap="large")

with k1:
    with st.container(border=True):
        st.markdown("#### Z-Score — Field Performance Score")
        st.markdown(
            """
            Measures how an athlete performed **relative to the field that day**, expressed in
            standard deviations from the field average.

            - **+1.0** = finished one standard deviation *better* than the average competitor
            - **0.0** = exactly average for the field
            - **−1.0** = one standard deviation *below* the field average

            Z-Score allows fair comparison across different races, venues, field sizes, and conditions.
            A +1.2 at Wengen and a +1.2 at a regional venue represent equally dominant performances
            *relative to who they were racing against that day*.
            """
        )

    with st.container(border=True):
        st.markdown("#### Strokes Gained")
        st.markdown(
            """
            Borrowed from golf analytics, this measures how many FIS points the athlete
            gained or lost **compared to the field average** in each race.

            - **Positive** = outperformed the field; beat the average competitor
            - **Negative** = lost ground to the field; below average finish
            - Accumulated over a career, it reveals consistent over- or under-performance
              regardless of result FIS points

            Unlike raw FIS points, strokes gained is not inflated or deflated by the quality
            of the field — it is always measured against whoever was racing that day.
            """
        )

    with st.container(border=True):
        st.markdown("#### Momentum")
        st.markdown(
            """
            A rolling average of recent Z-Scores showing whether an athlete's **current form
            is trending up or down**.

            - **Rising line** = improving form, recent races above season average
            - **Falling line** = cooling off, recent races below season average
            - **Above zero** = currently beating the field on average

            Momentum captures short-term form that season averages can hide. An athlete who
            starts a season strong and fades will have the same seasonal average as one who
            starts slow and peaks — but their momentum trends are opposite.
            """
        )

with k2:
    with st.container(border=True):
        st.markdown("#### Hill Difficulty Index (HDI)")
        st.markdown(
            """
            A composite **0–100 score** measuring how physically and technically demanding
            a course is. Higher = harder.

            | Component | Weight | What it captures |
            |---|---|---|
            | DNF Rate | 40% | Attrition — how often athletes fail to finish |
            | Vertical Drop | 20% | Elevation change, start to finish |
            | Winning Time | 20% | Longer races = more demanding |
            | Gate Count | 10% | More gates = more technical |
            | Start Altitude | 10% | Higher starts = thinner air, more exposure |

            Scores are normalized *within each discipline*, so Slalom and Downhill HDI scores
            are only comparable within their own event type, not across disciplines.
            """
        )

    with st.container(border=True):
        st.markdown("#### Best Courses")
        st.markdown(
            """
            Venues where athletes have historically posted their **best career performances**
            relative to the field.

            The score is the average Z-score of athletes' top career results at that venue.
            A high score means athletes tend to ski their personal bests there — whether
            due to terrain, course design, conditions, or tradition.

            This is **not** a difficulty measure — it is a *peak performance* measure.
            A high-scoring venue is one that brings out the best in athletes, not necessarily
            one that produces close finishes.
            """
        )

st.markdown("---")

# ── What the numbers mean in practice ────────────────────────────────────────
st.markdown("## Reading the Numbers — Practical Guide")
st.markdown(
    """
    | Metric | What a good value looks like | What a concerning value looks like |
    |---|---|---|
    | Race Z-Score | Above +0.5 consistently | Below −0.3 consistently |
    | Season Avg Z | +0.2 or higher | Negative over a full season |
    | Momentum | Rising above zero heading into a race block | Declining through the back half of a season |
    | HDI | 70+ = genuinely demanding course | Below 30 = technically straightforward |
    | DNF % | Below 10% = clean course | Above 25% = high-attrition course |
    | Bounce Back Rate | Above 50% after a bad race | Below 30% suggests struggle to recover form |

    **Important caveats:**
    - Z-Score comparisons are only valid *within* a discipline. Comparing a Slalom Z-Score to
      a Downhill Z-Score is not meaningful because the field compositions are different.
    - A very small field (under 20 athletes) makes Z-Scores and strokes gained less stable —
      one outlier can shift the whole distribution.
    - Course Similarity is computed within the same discipline. Results reflect similarity
      across physical and performance characteristics, not subjective feel.
    """
)

st.markdown("---")

# ── Data source ───────────────────────────────────────────────────────────────
st.markdown("## Data Source")
st.markdown(
    """
    All data is sourced from the **FIS** (Fédération Internationale de Ski et des Sports de Glisse),
    the international governing body of alpine ski racing. FIS publishes official race results,
    athlete FIS points, and course homologation data for every sanctioned World Cup, World
    Championship, and Europa Cup event.

    Data is processed and loaded automatically after each race weekend. The analytics pipeline
    computes derived metrics — Z-scores, strokes gained, momentum, HDI, course similarity — from
    the raw FIS results and course records.

    """
)

st.markdown("---")

# ── Footer ────────────────────────────────────────────────────────────────────
left, right = st.columns([3, 1])
with left:
    st.caption("Data sourced from FIS · Updated automatically after each race weekend")
with right:
    st.caption("Created by: Finnbahr Malcolm")
