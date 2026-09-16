import streamlit as st
from app.core.skill_gap_analyzer import run_skill_gap_analysis
from app.core.market_analyzer import run_market_analysis

st.set_page_config(page_title="Career Strategy", layout="wide")
st.title("Career Strategy Layer")
st.caption("Analyzes patterns across all collected jobs to identify skill gaps and market trends.")

tab1, tab2 = st.tabs(["Skill Gap Analysis", "Market Demand Snapshot"])

# ── Skill Gap Analysis ───────────────────────────────────────────
with tab1:
    st.subheader("Skill Gap Analysis")
    st.markdown("""
    This scans your collected job postings, extracts the specific skills and technologies mentioned,
    and compares them against your profile. Gaps are skills that appear frequently in postings
    but are not represented in your profile.
    """)

    verdict_options = st.multiselect(
        "Analyze jobs with verdict",
        ["Apply", "Consider", "Skip"],
        default=["Apply", "Consider"]
    )

    if st.button("Run Skill Gap Analysis", type="primary"):
        with st.spinner("Analyzing job postings... this may take a minute for larger datasets."):
            result = run_skill_gap_analysis(verdict_filter=verdict_options if verdict_options else None)
            st.session_state["skill_gap_result"] = result

    result = st.session_state.get("skill_gap_result")

    if result:
        if "error" in result:
            st.error(result["error"])
        else:
            st.success(f"Analyzed {result['total_jobs_analyzed']} job postings.")

            st.markdown("### Skill Gaps")
            st.caption("Skills mentioned frequently in target postings but not in your profile. These represent the highest-leverage areas to add evidence or pursue learning.")

            gaps = result.get("gaps", [])
            if not gaps:
                st.info("No significant gaps found. Your profile covers the skills appearing in these postings well.")
            else:
                for gap in gaps[:15]:
                    pct = (gap["frequency"] / gap["total_jobs_analyzed"]) * 100
                    st.markdown(f"**{gap['skill']}** — appears in approximately {pct:.0f}% of analyzed postings")

            st.divider()

            st.markdown("### Skills You're Covered On")
            st.caption("Skills frequently mentioned in postings that your profile already represents.")

            covered = result.get("covered", [])
            if covered:
                covered_text = ", ".join([c["skill"] for c in covered[:20]])
                st.markdown(covered_text)
            else:
                st.info("No strong overlaps found.")
    else:
        st.info("Click 'Run Skill Gap Analysis' to generate the report. This calls the AI to extract skills from job descriptions and may use a small amount of API credit.")

# ── Market Demand Snapshot ───────────────────────────────────────
with tab2:
    st.subheader("Market Demand Snapshot")
    st.markdown("A snapshot view of your collected job data. No AI calls, instant results.")

    if st.button("Generate Market Snapshot", type="primary"):
        result = run_market_analysis()
        st.session_state["market_result"] = result

    result = st.session_state.get("market_result")

    if result:
        if "error" in result:
            st.error(result["error"])
        else:
            col1, col2, col3 = st.columns(3)
            verdicts = result["verdict_breakdown"]
            col1.metric("Apply", verdicts.get("Apply", 0))
            col2.metric("Consider", verdicts.get("Consider", 0))
            col3.metric("Skip", verdicts.get("Skip", 0))

            st.divider()

            st.markdown("### Companies Posting Multiple Roles")
            st.caption("Companies appearing more than once may signal active expansion or hiring pushes.")
            repeat_companies = result.get("repeat_companies", [])
            if repeat_companies:
                for rc in repeat_companies:
                    st.markdown(f"- **{rc['company']}**: {rc['postings']} postings")
            else:
                st.info("No companies with multiple postings found yet.")

            st.divider()

            st.markdown("### Salary Signals")
            salary_stats = result.get("salary_stats")
            if salary_stats:
                st.markdown(f"**{salary_stats['jobs_with_salary_data']}** of **{salary_stats['total_jobs']}** postings include salary data.")
                st.markdown(f"Average range: **${salary_stats['avg_min']:,} - ${salary_stats['avg_max']:,}**")
                st.markdown(f"Overall range observed: **${salary_stats['overall_min']:,} - ${salary_stats['overall_max']:,}**")
                if "compensation_floor" in salary_stats:
                    st.markdown(f"Your compensation floor: **${salary_stats['compensation_floor']:,}**")
                    st.markdown(f"Postings with a max salary below your floor: **{salary_stats['postings_below_floor']}**")
            else:
                st.info("No salary data found in collected postings.")

            st.divider()

            st.markdown("### Remote vs Onsite Breakdown")
            remote_breakdown = result.get("remote_breakdown", {})
            for remote_type, count in remote_breakdown.items():
                st.markdown(f"- **{remote_type}**: {count}")

            st.divider()

            st.markdown("### Most Common Apply-Tier Title Patterns")
            st.caption("Rough grouping by the first few words of Apply-tier job titles.")
            for pattern, count in result.get("top_apply_title_patterns", []):
                st.markdown(f"- **{pattern}**: {count}")
    else:
        st.info("Click 'Generate Market Snapshot' to see the report.")