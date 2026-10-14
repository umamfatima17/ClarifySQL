
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import streamlit.components.v1 as components
from core.query_engine import answer_question, resolve_follow_up_question
from core.clarification_engine import detect_clarification
from core.session_store import (
    initialize_session_tables,
    create_session,
    add_session_message,
    update_session,
    get_session,
    list_pending_sessions,
)

from core.analytics import (
    get_overall_metrics,
    get_monthly_performance,
    get_product_performance,
)
from ui.styles import load_styles


st.set_page_config(
    page_title="ClarifySQL | Business Intelligence",
    page_icon="C",
    layout="wide",
    initial_sidebar_state="expanded",
)

load_styles()
initialize_session_tables()


def money(value):
    return f"₹{float(value):,.2f}"

def heading(title, subtitle=None):
    st.markdown(
        f'<div class="section-title">{title}</div>',
        unsafe_allow_html=True,
    )
    if subtitle:
        st.markdown(
            f'<div class="section-subtitle">{subtitle}</div>',
            unsafe_allow_html=True,
        )


def page_header(eyebrow, title, description):
    left, right = st.columns([5, 1.4], gap="medium")

    with left:
        st.markdown(
            f'<div class="eyebrow">{eyebrow}</div>',
            unsafe_allow_html=True,
        )
        st.title(title)
        st.markdown(
            f'<div class="page-description">{description}</div>',
            unsafe_allow_html=True,
        )

    with right:
        st.markdown(
            '<div style="text-align:right;padding-top:2px;">'
            '<span class="workspace-badge">SAMPLE WORKSPACE</span>'
            '</div>',
            unsafe_allow_html=True,
        )

    st.markdown('<div class="gold-rule"></div>', unsafe_allow_html=True)


def footer():
    st.markdown(
        """
        <div class="app-footer">
            <span><strong>ClarifySQL</strong> ·  Business Question Answering Assistant</span>
            <span>Demonstration workspace using synthetic sample sales data.</span>
        </div>
        """,
        unsafe_allow_html=True,
    )


def open_product_page():
    st.session_state["page"] = "Product Performance"


def sidebar():
    with st.sidebar:
        st.markdown(
            """
            <div class="brand">
                <div class="brand-logo">C</div>
                <div>
                    <div class="brand-name">ClarifySQL</div>
                    <div class="brand-tagline">Business intelligence, made clear</div>
                </div>
            </div>
            <div class="sidebar-heading">YOUR WORKSPACE</div>
            """,
            unsafe_allow_html=True,
        )

        page = st.radio(
            "Navigation",
            [
                "Business Overview",
                "Ask your data",
                "Product Performance",
            ],
            key="page",
            label_visibility="collapsed",
        )

        st.markdown(
            """
            <div class="sidebar-heading">CONNECTED DATA</div>
            <div class="dataset-card">
                <div class="dataset-title">Retail sales dataset</div>
                <div class="dataset-description">
                    Local SQLite database<br>
                    January - June 2026<br>
                    Synthetic demonstration data
                </div>
            </div>
            <div class="sidebar-footer">
                <strong>CLARIFYSQL · PROJECT EDITION</strong><br>
                Explore data. Ask better questions.<br>
                Local analytics workspace
            </div>
            """,
            unsafe_allow_html=True,
        )

    return page


def chart_layout(fig, height):
    fig.update_layout(
        height=height,
        margin=dict(l=5, r=12, t=10, b=8),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(
            family="Arial, sans-serif",
            size=12,
            color="#626E65",
        ),
        hoverlabel=dict(
            bgcolor="#FFFFFF",
            bordercolor="#E2E7E1",
            font_color="#202A24",
        ),
    )
    return fig


def format_month(value):
    value = str(value)
    try:
        return pd.to_datetime(value).strftime("%b %Y")
    except (ValueError, TypeError):
        return value


def overview():
    metrics = get_overall_metrics()
    monthly = pd.DataFrame(get_monthly_performance())
    products = pd.DataFrame(get_product_performance())

    page_header(
        "BUSINESS INTELLIGENCE / OVERVIEW",
        "Your business, in perspective.",
        "Understand sales performance, track profitability, and explore "
        "the numbers behind your business - all in one place.",
    )

    heading(
        "Performance at a glance",
        "A snapshot of completed sales in the sample dataset.",
    )

    k1, k2, k3, k4 = st.columns(4, gap="medium")

    with k1:
        st.metric("Total revenue", money(metrics["total_revenue"]))
    with k2:
        st.metric("Gross profit", money(metrics["total_profit"]))
    with k3:
        st.metric("Completed orders", f'{metrics["total_orders"]:,}')
    with k4:
        st.metric("Units sold", f'{metrics["units_sold"]:,}')

    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)

    chart_col, insight_col = st.columns([1.55, 1], gap="large")

    with chart_col:
        heading(
            "Revenue by month",
            "Monthly revenue from completed orders.",
        )

        if not monthly.empty and {"month", "revenue"}.issubset(monthly.columns):
            monthly = monthly.copy()
            monthly["revenue"] = pd.to_numeric(
                monthly["revenue"], errors="coerce"
            ).fillna(0)
            monthly["month_label"] = monthly["month"].map(format_month)

            highest = max(float(monthly["revenue"].max()), 1)
            axis_max = ((int(highest) // 10000) + 1) * 10000

            fig = go.Figure(
                go.Bar(
                    x=monthly["month_label"],
                    y=monthly["revenue"],
                    width=0.43,
                    marker=dict(
                        color="#2D5A43",
                        line=dict(width=0),
                    ),
                    hovertemplate=(
                        "<b>%{x}</b><br>"
                        "Revenue:INR %{y:,.2f}<extra></extra>"
                    ),
                )
            )

            fig.update_layout(
                showlegend=False,
                bargap=0.35,
                xaxis=dict(
                    title=None,
                    showgrid=False,
                    showline=True,
                    linecolor="#E2E7E1",
                    tickfont=dict(size=11, color="#46574A"),
                    tickangle=0,
                    automargin=True,
                ),
                yaxis=dict(
                    title=dict(text="Revenue (INR)", font=dict(size=11)),
                    range=[0, axis_max],
                    tickformat=",.0f",
                    nticks=6,
                    gridcolor="#E9EDE8",
                    zeroline=False,
                    tickfont=dict(size=10),
                ),
            )

            chart_layout(fig, 330)
            st.plotly_chart(
                fig,
                width="stretch",
                config={"displayModeBar": False, "responsive": True},
            )
        else:
            st.info("Monthly revenue data is not available.")

    with insight_col:
        heading(
            "What the numbers say",
            "Observations based on recorded results.",
        )

        if not monthly.empty and "revenue" in monthly.columns:
            monthly = monthly.copy()
            monthly["revenue"] = pd.to_numeric(
                monthly["revenue"], errors="coerce"
            ).fillna(0)

            best = monthly.loc[monthly["revenue"].idxmax()]
            best_month = format_month(best.get("month", ""))
            best_revenue = float(best["revenue"])

            st.markdown(
                f"""
                <div class="insight-card">
                    <div class="insight-label">REVENUE HIGHLIGHT</div>
                    <div class="insight-text">
                        The highest-revenue month was
                        <strong>{best_month}</strong>, with
                        <strong>{money(best_revenue)}</strong>
                        in completed sales.
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            if len(monthly) >= 2:
                previous = float(monthly.iloc[-2]["revenue"])
                latest = float(monthly.iloc[-1]["revenue"])

                if previous:
                    change = ((latest - previous) / previous) * 100

                    if change < 0:
                        recent_text = (
                            f"Revenue decreased by {abs(change):.1f}% "
                            "between the two most recent periods."
                        )
                    elif change > 0:
                        recent_text = (
                            f"Revenue increased by {change:.1f}% "
                            "between the two most recent periods."
                        )
                    else:
                        recent_text = (
                            "Revenue remained unchanged between the "
                            "two most recent periods."
                        )

                    st.markdown(
                        f"""
                        <div class="insight-card secondary">
                            <div class="insight-label">RECENT PERFORMANCE</div>
                            <div class="insight-text">{recent_text}</div>
                        </div>
                        <div class="insight-note">
                            Observed change does not establish its cause.
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

        st.button(
            "Explore product performance -> ",
            key="explore_products",
            width="stretch",
            on_click=open_product_page,
        )

    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)

    heading(
        "Products contributing to sales",
        "Top five products ranked by recorded revenue.",
    )

    if not products.empty and {
        "product_name", "revenue"
    }.issubset(products.columns):
        products = products.copy()
        products["revenue"] = pd.to_numeric(
            products["revenue"], errors="coerce"
        ).fillna(0)

        top = products.nlargest(5, "revenue").sort_values(
            "revenue", ascending=True
        )

        highest = max(float(top["revenue"].max()), 1)
        axis_max = ((int(highest) // 10000) + 1) * 10000

        fig = go.Figure(
            go.Bar(
                x=top["revenue"],
                y=top["product_name"],
                orientation="h",
                width=0.52,
                marker=dict(
                    color="#2D5A43",
                    line=dict(width=0),
                ),
                hovertemplate=(
                    "<b>%{y}</b><br>"
                    "Revenue:INR %{x:,.2f}<extra></extra>"
                ),
            )
        )

        fig.update_layout(
            showlegend=False,
            bargap=0.32,
            xaxis=dict(
                title=dict(text="Revenue (INR)", font=dict(size=11)),
                range=[0, axis_max],
                tickformat=",.0f",
                nticks=7,
                gridcolor="#E9EDE8",
                zeroline=False,
                tickfont=dict(size=11),
            ),
            yaxis=dict(
                title=None,
                showgrid=False,
                automargin=True,
                tickfont=dict(size=12, color="#34473A"),
            ),
        )

        chart_layout(fig, 265)
        st.plotly_chart(
            fig,
            width="stretch",
            config={"displayModeBar": False, "responsive": True},
        )
    else:
        st.info("Product performance data is not available.")

    footer()


def product_performance():
    page_header(
        "BUSINESS INTELLIGENCE / PRODUCT ANALYSIS",
        "Know your products.",
        "Compare product revenue, gross profit and units sold using "
        "completed orders from the retail sales dataset.",
    )

    products = pd.DataFrame(get_product_performance())

    if products.empty:
        st.info("No product data is available.")
        footer()
        return

    required = {
        "product_name", "category", "units_sold", "revenue", "profit"
    }

    if not required.issubset(products.columns):
        st.error("The product analytics result has an unexpected structure.")
        footer()
        return

    for column in ["units_sold", "revenue", "profit"]:
        products[column] = pd.to_numeric(
            products[column], errors="coerce"
        ).fillna(0)

    c1, c2, c3 = st.columns(3, gap="medium")
    c1.metric("Product revenue", money(products["revenue"].sum()))
    c2.metric("Gross profit", money(products["profit"].sum()))
    c3.metric("Units sold", f'{products["units_sold"].sum():,.0f}')

    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)

    left, right = st.columns(2, gap="large")

    for column, title, subtitle, color, axis_title in [
        (left, "Revenue by product", "Ranked by recorded revenue.",
         "#2D5A43", "Revenue (INR)"),
        (right, "Gross profit by product", "Revenue less product cost.",
         "#B69A62", "Gross profit (INR)"),
    ]:
        with column:
            heading(title, subtitle)
            metric = "revenue" if title == "Revenue by product" else "profit"
            data = products.sort_values(metric, ascending=True)

            fig = go.Figure(
                go.Bar(
                    x=data[metric],
                    y=data["product_name"],
                    orientation="h",
                    width=0.52,
                    marker_color=color,
                    hovertemplate=(
                        "<b>%{y}</b><br>"
                        f"{axis_title}: INR %{{x:,.2f}}<extra></extra>"
                    ),
                )
            )
            fig.update_layout(
                showlegend=False,
                xaxis=dict(
                    title=axis_title,
                    tickformat=",.0f",
                    gridcolor="#E9EDE8",
                ),
                yaxis=dict(title=None, showgrid=False, automargin=True),
            )
            chart_layout(fig, 350)
            st.plotly_chart(
                fig,
                width="stretch",
                config={"displayModeBar": False, "responsive": True},
            )

    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
    heading(
        "Product performance register",
        "Detailed figures for every product.",
    )

    table = products[
        ["product_name", "category", "units_sold", "revenue", "profit"]
    ].sort_values("revenue", ascending=False).rename(
        columns={
            "product_name": "Product",
            "category": "Category",
            "units_sold": "Units sold",
            "revenue": "Revenue",
            "profit": "Gross profit",
        }
    )

    st.dataframe(
        table,
        width="stretch",
        hide_index=True,
        column_config={
            "Units sold": st.column_config.NumberColumn(format="%d"),
            "Revenue": st.column_config.NumberColumn(format="INR%.2f"),
            "Gross profit": st.column_config.NumberColumn(format="INR%.2f"),
        },
    )

    footer()


def ask_your_data():
    page_header(
        "BUSINESS INTELLIGENCE / QUESTION WORKSPACE",
        "What would you like to know?",
        "Explore business data using natural-language questions instead "
        "of writing SQL by hand.",
    )

    examples = [
        "Which product generated the most revenue?",
        "Compare monthly revenue.",
        "Which product has the highest gross profit?",
        "What is the total revenue?",
        "How many units were sold?",
        "Show the top 5 products by revenue.",
        "Compare revenue by category.",
        "How many orders were cancelled?",
    ]

    def apply_example():
        selected = st.session_state.get("question_example", "")
        st.session_state["business_question"] = (
            selected if selected in examples else ""
        )

    if "business_question" not in st.session_state:
        st.session_state["business_question"] = ""

    if "query_result" not in st.session_state:
        st.session_state["query_result"] = None

    if "scroll_to_result" not in st.session_state:
        st.session_state["scroll_to_result"] = False

    if "scroll_run_id" not in st.session_state:
        st.session_state["scroll_run_id"] = 0

    saved_sessions = list_pending_sessions()
    if saved_sessions:
        st.markdown("**Resume a saved clarification**")
        session_labels = {
            item["original_question"]:
                item["session_id"]
            for item in saved_sessions
        }
        selected_saved = st.selectbox(
            "Saved questions",
            ["Choose a saved question..."] + list(session_labels),
            key="saved_clarification_session",
        )
        if st.button("Resume clarification"):
            if selected_saved in session_labels:
                saved_session = get_session(
                    session_labels[selected_saved]
                )
                if saved_session:
                    saved_result = saved_session["context"].get("result")
                    if saved_result:
                        st.session_state["active_session_id"] = (
                            session_labels[selected_saved]
                        )
                        st.session_state["query_result"] = saved_result
                        st.session_state["scroll_to_result"] = True
                        st.rerun()
                    else:
                        st.warning(
                            "This saved session has no resumable question."
                        )


    left, right = st.columns([1.5, 1], gap="large")

    with left:
        heading(
            "Ask a business question",
            "Choose an example or enter your own question.",
        )

        st.selectbox(
            "Suggested questions",
            ["Choose an example..."] + examples,
            key="question_example",
            on_change=apply_example,
        )

        question = st.text_area(
            "Your question",
            placeholder="Ask a question about sales or products...",
            height=130,
            key="business_question",
        )

        if st.button(
            "Analyze question",
            width="stretch",
            type="primary",
        ):
            st.session_state["scroll_run_id"] += 1
            st.session_state["scroll_to_result"] = True
            st.session_state["active_session_id"] = None

            submitted_question = st.session_state.get(
                "business_question", ""
            ).strip()

            if not submitted_question:
                st.session_state["query_result"] = {
                    "error": "Please enter a business question."
                }
            else:
                try:
                    previous_question = st.session_state.get(
                        "last_successful_question", ""
                    )
                    resolved_question = resolve_follow_up_question(
                        submitted_question, previous_question
                    )
                    clarification = detect_clarification(resolved_question)

                    if clarification:
                        pending_result = {
                            "clarification": clarification,
                            "submitted_question": submitted_question,
                            "clarification_history": [],
                        }
                        session_id = create_session(
                            submitted_question,
                            context={"result": pending_result},
                        )
                        pending_result["session_id"] = session_id
                        st.session_state["active_session_id"] = session_id
                        update_session(
                            session_id,
                            context={"result": pending_result},
                        )
                        add_session_message(
                            session_id,
                            "assistant",
                            clarification.get("prompt", "Clarification required"),
                        )
                        st.session_state["query_result"] = pending_result
                    else:
                        with st.spinner(
                            "Interpreting question and querying data..."
                        ):
                            result = answer_question(resolved_question)
                            result["submitted_question"] = submitted_question
                            st.session_state["query_result"] = result

                            has_answer_errors = any(
                                item.get("error")
                                for item in result.get("answers", [])
                            )
                            if not result.get("error") and not has_answer_errors:
                                st.session_state["last_successful_question"] = (
                                    resolved_question
                                )
                except ValueError as exc:
                    message = str(exc)
                    if "What do you mean by 'best' product?" in message:
                        st.session_state["query_result"] = {
                            "clarification": {
                                "prompt": message,
                                "options": [
                                    "Revenue",
                                    "Gross profit",
                                    "Units sold",
                                ],
                            },
                            "submitted_question": submitted_question,
                        }
                    else:
                        st.session_state["query_result"] = {
                            "error": message
                        }
                except Exception:
                    st.session_state["query_result"] = {
                        "error": (
                            "Something went wrong while processing the "
                            "question. Please try again."
                        )
                    }

    with right:
        heading(
            "Questions worth exploring",
            "Examples of supported business questions.",
        )

        for index, item in enumerate(examples, start=1):
            st.markdown(
                f"""
                <div class="insight-card">
                    <div class="insight-label">EXAMPLE {index:02d}</div>
                    <div class="insight-text">{item}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    result = st.session_state.get("query_result")

    active_session_id = st.session_state.get("active_session_id")
    if result and active_session_id and not result.get("clarification"):
        saved_session = get_session(active_session_id)
        if saved_session and saved_session["status"] == "pending":
            has_error = bool(result.get("error")) or any(
                item.get("error") for item in result.get("answers", [])
            )
            add_session_message(
                active_session_id,
                "assistant",
                "Clarification ended with an error."
                if has_error else "Clarification completed successfully.",
            )
            update_session(
                active_session_id,
                status="error" if has_error else "completed",
                context={
                    "submitted_question": result.get("submitted_question", ""),
                    "clarification_history": result.get("clarification_history", []),
                },
            )

    if result:
        st.markdown(
            '<div id="query-results-anchor"></div>',
            unsafe_allow_html=True,
        )

        if st.session_state.get("scroll_to_result"):
            scroll_id = st.session_state["scroll_run_id"]
            st.html(
                f"""
                <script>
                (() => {{
                    const runId = {scroll_id};

                    function scrollToAnswer(attempt = 0) {{
                        const target = document.getElementById(
                            "query-results-anchor"
                        );

                        if (target) {{
                            target.scrollIntoView({{
                                behavior: "smooth",
                                block: "start"
                            }});
                        }} else if (attempt < 30) {{
                            setTimeout(
                                () => scrollToAnswer(attempt + 1),
                                150
                            );
                        }}
                    }}

                    setTimeout(() => scrollToAnswer(), 100);
                    setTimeout(() => scrollToAnswer(), 500);
                    setTimeout(() => scrollToAnswer(), 1000);
                }})();
                </script>
                """,
                unsafe_allow_javascript=True,
            )
            st.session_state["scroll_to_result"] = False

        st.markdown(
            '<hr class="section-divider">',
            unsafe_allow_html=True,
        )

        heading(
            "Your answer",
            "Insights generated from your local retail sales database.",
        )

        if result.get("clarification"):
            clarification = result["clarification"]
            step = clarification.get("step", 1)

            st.info(clarification["prompt"])

            if step == 2:
                st.markdown("**How many products would you like to see?**")
                selected_scope = st.radio(
                    "Choose result size",
                    clarification["options"],
                    key="clarification_scope_step2",
                    horizontal=True,
                    label_visibility="collapsed",
                )

                if st.button(
                    "Show results",
                    key="resolve_product_scope",
                    type="primary",
                ):
                    metric = (
                        result.get("clarification_history", ["Revenue"])[0]
                    )
                    if metric == "Units sold":
                        clarified_questions = {
                            "Top product only": "Which product sold the most units?",
                            "Top 5 products": "Show the top 5 products by units sold.",
                        }
                    elif metric == "Gross profit":
                        clarified_questions = {
                            "Top product only": "Which product has the highest gross profit?",
                            "Top 5 products": "Show the top 5 products by gross profit.",
                        }
                    else:
                        clarified_questions = {
                            "Top product only": "Which product generated the most revenue?",
                            "Top 5 products": "Show the top 5 products by revenue.",
                        }
                    clarified_question = clarified_questions.get(selected_scope)

                    if not clarified_question:
                        st.error(
                            "Please select a supported result size and try again."
                        )
                    else:
                        try:
                            with st.spinner("Running the clarified question..."):
                                clarified_result = answer_question(
                                    clarified_question,
                                    filter_context=result.get("submitted_question", ""),
                                )

                            history = list(
                                result.get("clarification_history", [])
                            )
                            history.append(selected_scope)

                            clarified_result["submitted_question"] = (
                                result.get("submitted_question", "")
                            )
                            clarified_result["clarification_history"] = history
                            clarified_result["clarification_choice"] = (
                                " -> ".join(history)
                            )

                            st.session_state["query_result"] = clarified_result
                            st.session_state["last_successful_question"] = (
                                clarified_question
                            )
                            st.rerun()
                        except Exception:
                            st.error(
                                "The clarified question could not be completed. "
                                "Please try again."
                            )

            else:
                original_question = (
                    result.get("submitted_question", "").lower()
                )
                if any(
                    phrase in original_question
                    for phrase in (
                        "top-selling",
                        "top selling",
                        "best-selling",
                        "best selling",
                    )
                ):
                    st.markdown(
                        "**Choose a ranking metric for top-selling products.**"
                    )
                else:
                    st.markdown(
                        "**How would you like to define 'best'?**"
                    )
                selected_metric = st.radio(
                    "Choose a comparison metric",
                    clarification["options"],
                    key="clarification_metric_step1",
                    horizontal=True,
                    label_visibility="collapsed",
                )

                if st.button(
                    "Continue",
                    key="resolve_product_clarification",
                    type="primary",
                ):
                    current_result = st.session_state["query_result"]

                    if selected_metric in ("Revenue", "Gross profit", "Units sold"):
                        next_clarification = detect_clarification(
                            current_result.get("submitted_question", ""),
                            answers=[selected_metric],
                        )
                        if next_clarification:
                            current_result["clarification"] = next_clarification
                            current_result["clarification_history"] = [
                                selected_metric
                            ]
                            session_id = current_result.get("session_id")
                            if session_id:
                                add_session_message(
                                    session_id, "user", selected_metric
                                )
                                update_session(
                                    session_id,
                                    context={"result": current_result},
                                )
                                add_session_message(
                                    session_id,
                                    "assistant",
                                    next_clarification.get("prompt", ""),
                                )
                            st.session_state["query_result"] = current_result
                            st.rerun()
                        else:
                            st.error(
                                "This clarification path is not supported yet."
                            )

                    elif selected_metric == "Units sold":
                        original_question = current_result.get(
                            "submitted_question", ""
                        ).lower()

                        is_top_five = any(
                            phrase in original_question
                            for phrase in (
                                "top selling",
                                "top-selling",
                                "best selling",
                                "best-selling",
                                "top sellers",
                                "best-selling items",
                                "top selling items",
                            )
                        )

                        clarified_question = (
                            "Show the top 5 products by units sold."
                            if is_top_five
                            else "Which product sold the most units?"
                        )

                        try:
                            with st.spinner(
                                "Running the clarified question..."
                            ):
                                clarified_result = answer_question(
                                    clarified_question,
                                    filter_context=current_result.get("submitted_question", ""),
                                )

                            clarified_result["submitted_question"] = (
                                current_result.get("submitted_question", "")
                            )
                            clarified_result["clarification_history"] = [
                                selected_metric
                            ]
                            clarified_result["clarification_choice"] = (
                                selected_metric
                            )
                            st.session_state["query_result"] = clarified_result
                            st.session_state["last_successful_question"] = (
                                clarified_question
                            )
                            st.rerun()
                        except Exception as exc:
                            st.error(
                                f"Could not complete the clarified question: {exc}"
                            )

                    else:
                        clarified_questions = {
                            "Gross profit":
                                "Which product has the highest gross profit?",
                        }
                        clarified_question = clarified_questions.get(selected_metric)

                        if not clarified_question:
                            st.error(
                                "This comparison metric is not supported yet. "
                                "Please choose another option."
                            )
                            st.stop()

                        try:
                            with st.spinner(
                                "Running the clarified question..."
                            ):
                                clarified_result = answer_question(
                                    clarified_question,
                                    filter_context=current_result.get("submitted_question", ""),
                                )

                            clarified_result["submitted_question"] = (
                                current_result.get("submitted_question", "")
                            )
                            clarified_result["clarification_history"] = [
                                selected_metric
                            ]
                            clarified_result["clarification_choice"] = (
                                selected_metric
                            )

                            st.session_state["query_result"] = clarified_result
                            st.session_state["last_successful_question"] = (
                                clarified_question
                            )
                            st.rerun()
                        except Exception:
                            st.error(
                                "The clarified question could not be "
                                "completed. Please try again."
                            )

        elif result.get("error"):
            st.error(result["error"])
        else:
            if result.get("clarification_history"):
                st.caption(
                    "Clarifications applied: "
                    + " -> ".join(result["clarification_history"])
                )

            answers = result.get("answers", [])

            if len(answers) > 1:
                heading(
                    "Question-by-question results",
                    "Each question is evaluated separately, with relevant follow-up context preserved.",
                )

                for index, answer in enumerate(answers, start=1):
                    with st.container(border=True):
                        st.markdown(
                            f"**{index}. {answer['question']}**"
                        )

                        if answer.get("error"):
                            st.warning(answer["error"])
                        else:
                            st.caption(answer["interpretation"])
                            if answer.get("intent") == "ai_generated_select":
                                st.info("AI-assisted answer - SQL validated before execution")

                            with st.expander("Explain this result", expanded=False):
                                st.markdown("**Question understood by the system**")
                                st.write(
                                    answer.get("resolved_question")
                                    or answer.get("question", "")
                                )

                                st.markdown("**Detected intent**")
                                st.code(
                                    answer.get("intent") or "Not available",
                                    language="text",
                                )

                                context = answer.get("follow_up_context")
                                st.markdown("**Follow-up context**")
                                st.write(
                                    f"Resolved using previous question: {context}"
                                    if context
                                    else "No previous-question context was needed."
                                )

                                status_cols = st.columns(2)
                                status_cols[0].markdown("**SQL validation**")
                                status_cols[0].success(
                                    answer.get("validation_status", "Not available")
                                )
                                status_cols[1].markdown("**Query execution**")
                                status_cols[1].success(
                                    answer.get("execution_status", "Not available")
                                )

                                if answer.get("sql"):
                                    st.markdown("**SQL executed**")
                                    st.code(answer["sql"], language="sql")
                                else:
                                    st.info("No SQL query was executed.")

                            if answer.get("rows"):
                                answer_df = pd.DataFrame(
                                    answer["rows"],
                                    columns=answer["columns"],
                                )

                                for _, answer_row in answer_df.iterrows():
                                    metric_cols = st.columns(
                                        min(max(len(answer_df.columns), 1), 3),
                                        gap="medium",
                                    )

                                    for col_index, column in enumerate(
                                        answer_df.columns
                                    ):
                                        value = answer_row[column]

                                        if pd.isna(value):
                                            display_value = "?"
                                        elif isinstance(value, (int, float)):
                                            if any(
                                                word in str(column).lower()
                                                for word in (
                                                    "revenue", "profit", "cost",
                                                    "sales", "amount"
                                                )
                                            ):
                                                display_value = money(value)
                                            else:
                                                display_value = (
                                                    f"{value:,.2f}"
                                                    .rstrip("0").rstrip(".")
                                                )
                                        else:
                                            display_value = str(value)

                                        with metric_cols[
                                            col_index % len(metric_cols)
                                        ]:
                                            st.metric(
                                                label=str(column).replace(
                                                    "_", " "
                                                ).title(),
                                                value=display_value,
                                            )
                            else:
                                st.info(
                                    "The query ran successfully, but no "
                                    "matching rows were returned."
                                )

            st.markdown(
                f"""
                <div style="
                    background: linear-gradient(120deg, #F0F5EF, #FAF9F4);
                    border: 1px solid #DCE6DA;
                    border-left: 5px solid #2D5A43;
                    border-radius: 12px;
                    padding: 20px 22px;
                    margin: 12px 0 20px 0;
                ">
                    <div style="
                        font-size: 11px;
                        font-weight: 700;
                        letter-spacing: 1.5px;
                        color: #55735D;
                        margin-bottom: 8px;
                    ">QUESTION INTERPRETED</div>
                    <div style="
                        font-size: 19px;
                        font-weight: 600;
                        color: #203B2B;
                        line-height: 1.5;
                    ">{result["interpretation"]}</div>
                    <div style="
                        font-size: 12px;
                        color: #657468;
                        margin-top: 8px;
                    ">Based on completed sales unless otherwise specified.</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            with st.expander("Explain this result", expanded=False):
                st.markdown("**Question understood by the system**")
                st.write(
                    result.get("resolved_question")
                    or result.get("question", "")
                )

                st.markdown("**Detected intent**")
                st.code(
                    result.get("intent") or "Not available",
                    language="text",
                )
                if result.get("intent") == "ai_generated_select":
                    st.info("AI-assisted answer - SQL validated before execution")

                context = result.get("follow_up_context")
                st.markdown("**Follow-up context**")
                st.write(
                    f"Resolved using previous question: {context}"
                    if context
                    else "No previous-question context was needed."
                )

                status_cols = st.columns(2)
                status_cols[0].markdown("**SQL validation**")
                validation_status = result.get(
                    "validation_status", "Not available"
                )
                if validation_status == "Passed":
                    status_cols[0].success(validation_status)
                else:
                    status_cols[0].info(validation_status)

                status_cols[1].markdown("**Query execution**")
                execution_status = result.get(
                    "execution_status", "Not available"
                )
                if execution_status == "Succeeded":
                    status_cols[1].success(execution_status)
                else:
                    status_cols[1].info(execution_status)

                if result.get("sql"):
                    st.markdown("**SQL executed**")
                    st.code(result["sql"], language="sql")
                else:
                    st.info("No SQL query was executed.")

            rows = result["rows"]
            columns = result["columns"]

            if (
                result.get("intent") == "product_revenue_by_date"
                and rows
                and "revenue" in columns
                and all(
                    row[columns.index("revenue")] == 0
                    for row in rows
                )
            ):
                st.info(
                    "No completed sales records were found for this product "
                    "in the selected date range."
                )

            if rows:
                result_df = pd.DataFrame(rows, columns=columns)

                if (
                    result.get("intent") == "compare_monthly_revenue"
                    and len(result_df) == 1
                    and {
                        "first_month",
                        "first_month_revenue",
                        "second_month",
                        "second_month_revenue",
                        "revenue_change",
                        "percentage_change",
                    }.issubset(result_df.columns)
                ):
                    record = result_df.iloc[0]
                    first_month = str(record["first_month"])
                    second_month = str(record["second_month"])
                    first_revenue = record["first_month_revenue"]
                    second_revenue = record["second_month_revenue"]
                    revenue_change = record["revenue_change"]
                    percentage_change = record["percentage_change"]

                    change_color = (
                        "#C62828" if pd.notna(revenue_change) and revenue_change < 0
                        else "#218653"
                    )
                    change_label = (
                        "Revenue decreased" if pd.notna(revenue_change) and revenue_change < 0
                        else "Revenue increased" if pd.notna(revenue_change) and revenue_change > 0
                        else "No revenue change"
                    )
                    percentage_text = (
                        f"{percentage_change:+.2f}%"
                        if pd.notna(percentage_change) else "?"
                    )

                    card_cols = st.columns(3, gap="medium")
                    card_data = [
                        (f"{first_month} Revenue", money(first_revenue), "#245A3D"),
                        (f"{second_month} Revenue", money(second_revenue), "#245A3D"),
                        ("Revenue Change", money(revenue_change), change_color),
                    ]

                    for card_col, (card_title, card_value, value_color) in zip(card_cols, card_data):
                        with card_col:
                            st.markdown(
                                f"""
                                <div style="
                                    background: #FFFFFF;
                                    border: 1px solid #DCE5DE;
                                    border-top: 4px solid {value_color};
                                    border-radius: 14px;
                                    padding: 20px 18px;
                                    min-height: 128px;
                                    box-shadow: 0 3px 12px rgba(36,75,58,0.06);
                                ">
                                    <div style="
                                        color: #718075;
                                        font-size: 12px;
                                        font-weight: 600;
                                        margin-bottom: 14px;
                                    ">{card_title}</div>
                                    <div style="
                                        color: {value_color};
                                        font-size: 25px;
                                        font-weight: 750;
                                        overflow-wrap: anywhere;
                                    ">{card_value}</div>
                                    {f'<div style="color:{change_color};font-size:13px;font-weight:700;margin-top:8px;">{percentage_text} &middot; {change_label}</div>' if card_title == "Revenue Change" else ""}
                                </div>
                                """,
                                unsafe_allow_html=True,
                            )

                elif len(result_df) == 1:
                    record = result_df.iloc[0]
                    metric_items = []
                elif len(result_df) == 1:
                    record = result_df.iloc[0]
                    metric_items = []

                    for column in result_df.columns:
                        value = record[column]

                        if pd.isna(value):
                            display_value = "â€”"
                        elif isinstance(value, (int, float)):
                            if any(
                                word in column.lower()
                                for word in ("revenue", "profit", "cost")
                            ):
                                display_value = money(value)
                            else:
                                display_value = (
                                    f"{value:,.2f}".rstrip("0").rstrip(".")
                                )
                        else:
                            display_value = str(value)

                        metric_items.append((column, display_value))

                    metric_cols = st.columns(
                        min(max(len(metric_items), 1), 3),
                        gap="medium",
                    )

                    for index, (label, value) in enumerate(metric_items):
                        with metric_cols[index % len(metric_cols)]:
                            st.markdown(
                                f"""
                                <div style="
                                    background: #FFFFFF;
                                    border: 1px solid #E1E7DF;
                                    border-radius: 12px;
                                    padding: 18px 16px;
                                    min-height: 105px;
                                    margin-bottom: 12px;
                                ">
                                    <div style="
                                        color: #718075;
                                        font-size: 12px;
                                        margin-bottom: 12px;
                                        text-transform: capitalize;
                                    ">{label.replace("_", " ")}</div>
                                    <div style="
                                        color: #254B35;
                                        font-size: 23px;
                                        font-weight: 700;
                                        overflow-wrap: anywhere;
                                    ">{value}</div>
                                </div>
                                """,
                                unsafe_allow_html=True,
                            )
                else:
                    st.markdown(
                        f"""
                        <div style="
                            color: #355E43;
                            font-size: 14px;
                            font-weight: 600;
                            margin: 12px 0;
                        ">&#10003; {len(result_df)} records found</div>
                        """,
                        unsafe_allow_html=True,
                    )

                heading(
                    "Result details",
                    "Values returned by the validated SQL query.",
                )

                display_df = result_df.copy()

                for column in display_df.columns:
                    if any(
                        word in column.lower()
                        for word in ("revenue", "profit", "cost")
                    ):
                        display_df[column] = display_df[column].map(
                            lambda value: (
                                money(value) if pd.notna(value) else "â€”"
                            )
                        )

                # Polished styling for business query results.
                styled_df = display_df.style.set_table_styles(
                    [
                        {
                            "selector": "th",
                            "props": [
                                ("background-color", "#244B3A"),
                                ("color", "#FFFFFF"),
                                ("font-weight", "700"),
                                ("font-size", "13px"),
                                ("padding", "12px 14px"),
                                ("border-bottom", "3px solid #D6B56D"),
                                ("text-align", "left"),
                            ],
                        },
                        {
                            "selector": "td",
                            "props": [
                                ("font-size", "13px"),
                                ("padding", "11px 14px"),
                                ("border-bottom", "1px solid #DCE5DE"),
                                ("color", "#26382D"),
                                ("text-align", "left"),
                            ],
                        },
                        {
                            "selector": "tbody tr:nth-child(even)",
                            "props": [("background-color", "#F1F6F2")],
                        },
                        {
                            "selector": "tbody tr:hover",
                            "props": [("background-color", "#E6F1E8")],
                        },
                    ],
                    overwrite=False,
                )

                # Emphasize key business figures.
                for column in display_df.columns:
                    column_name = str(column).lower()

                    if any(
                        word in column_name
                        for word in ("revenue", "profit", "amount", "sales", "total")
                    ):
                        styled_df = styled_df.set_properties(
                            subset=[column],
                            **{
                                "font-weight": "700",
                                "color": "#245A3D",
                                "background-color": "#E6F1E8",
                            },
                        )

                # Explicitly format comparison values for reliable display.
                if result.get("intent") == "compare_monthly_revenue":
                    if "revenue_change" in display_df.columns:
                        display_df["revenue_change"] = result_df[
                            "revenue_change"
                        ].map(
                            lambda value: "?" if pd.isna(value) else money(value)
                        )
                    if "percentage_change" in display_df.columns:
                        display_df["percentage_change"] = result_df[
                            "percentage_change"
                        ].map(
                            lambda value: (
                                "?" if pd.isna(value) else f"{value:+.2f}%"
                            )
                        )

                # Render displayed values as text so single-number SQL
                # results are left-aligned instead of right-aligned.
                left_aligned_df = display_df.copy()
                for column in left_aligned_df.columns:
                    left_aligned_df[column] = left_aligned_df[column].map(
                        lambda value: "" if value is None else str(value)
                    )

                # Preserve the existing table styling on the display copy.
                left_styled_df = left_aligned_df.style.set_table_styles(
                    [
                        {
                            "selector": "th",
                            "props": [
                                ("background-color", "#244B3A"),
                                ("color", "#FFFFFF"),
                                ("font-weight", "700"),
                                ("padding", "12px 14px"),
                                ("text-align", "left"),
                            ],
                        },
                        {
                            "selector": "td",
                            "props": [
                                ("text-align", "left"),
                                ("padding", "11px 14px"),
                            ],
                        },
                    ],
                    overwrite=False,
                )

                # Build cell-level styles from the original numeric results.
                # This remains reliable even when currency values are strings
                # in the displayed dataframe.
                negative_styles = pd.DataFrame(
                    "",
                    index=left_aligned_df.index,
                    columns=left_aligned_df.columns,
                )

                for column in result_df.columns:
                    if pd.api.types.is_numeric_dtype(result_df[column]):
                        for row_index, numeric_value in result_df[column].items():
                            if pd.notna(numeric_value) and numeric_value < 0:
                                negative_styles.loc[row_index, column] = (
                                    "color: #C62828 !important; "
                                    "font-weight: 700 !important;"
                                )

                # Apply per-cell styles without changing displayed values.
                left_styled_df = left_aligned_df.style.apply(
                    lambda _: negative_styles,
                    axis=None,
                ).set_table_styles(
                    [
                        {
                            "selector": "th",
                            "props": [
                                ("background-color", "#244B3A"),
                                ("color", "#FFFFFF"),
                                ("font-weight", "700"),
                                ("padding", "12px 14px"),
                                ("text-align", "left"),
                            ],
                        },
                        {
                            "selector": "td",
                            "props": [
                                ("text-align", "left"),
                                ("padding", "11px 14px"),
                                ("border-bottom", "1px solid #DCE5DE"),
                            ],
                        },
                    ],
                    overwrite=False,
                )

                if result.get("intent") == "compare_monthly_revenue":
                    import html as _html

                    headers = "".join(
                        "<th style='background:#244B3A;color:white;"
                        "padding:12px;text-align:left;'>"
                        + _html.escape(str(col).replace("_", " ").title())
                        + "</th>"
                        for col in result_df.columns
                    )

                    body_rows = []
                    for row_index, record in result_df.iterrows():
                        cells = []
                        for column in result_df.columns:
                            value = record[column]

                            if pd.isna(value):
                                shown = "?"
                            elif column == "percentage_change":
                                shown = f"{float(value):+.2f}%"
                            elif column in (
                                "first_month_revenue",
                                "second_month_revenue",
                                "revenue_change",
                            ):
                                shown = money(value)
                            else:
                                shown = str(value)

                            negative = (
                                pd.api.types.is_number(value)
                                and float(value) < 0
                            )
                            color = "#C62828" if negative else "#26382D"
                            weight = "700" if negative else "400"

                            cells.append(
                                "<td style='padding:11px 12px;"
                                "border-bottom:1px solid #DCE5DE;"
                                f"color:{color};font-weight:{weight};'>"
                                + _html.escape(str(shown))
                                + "</td>"
                            )

                        row_bg = "#F1F6F2" if row_index % 2 == 0 else "#FFFFFF"
                        body_rows.append(
                            f"<tr style='background:{row_bg}'>"
                            + "".join(cells)
                            + "</tr>"
                        )

                    table_html = (
                        "<div style='overflow-x:auto;width:100%'>"
                        "<table style='border-collapse:collapse;width:100%;"
                        "font-size:13px'>"
                        "<thead><tr>" + headers + "</tr></thead>"
                        "<tbody>" + "".join(body_rows) + "</tbody>"
                        "</table></div>"
                    )
                    st.markdown(table_html, unsafe_allow_html=True)
                else:
                    st.dataframe(
                        left_styled_df,
                        width="stretch",
                        hide_index=True,
                    )
            else:
                st.info(
                    "The query ran successfully, but no matching rows "
                    "were returned."
                )

            with st.expander("View SQL query", expanded=False):
                st.caption(
                    "Validated, read-only SQL executed against the database."
                )
                with st.container(key="sql_query_display"):
                    st.markdown(
                        """
                        <style>
                        .st-key-sql_query_display .stCodeBlock pre,
                        .st-key-sql_query_display .stCodeBlock code {
                            font-size: 0.82rem !important;
                            line-height: 1.35 !important;
                        }
                        
                        .st-key-sql_query_display .stCodeBlock pre,
                        .st-key-sql_query_display .stCodeBlock code {
                            font-size: 12px !important;
                            line-height: 1.45 !important;
                        }
</style>
                        """,
                        unsafe_allow_html=True,
                    )
                    st.code(
                        result["sql"],
                        language="sql",
                        line_numbers=True,
                        wrap_lines=True,
                    )

    st.markdown(
        """
        <div style="
            border-top: 1px solid #E5E9E3;
            padding-top: 12px;
            margin-top: 26px;
            color: #7A857C;
            font-size: 12px;
        ">
            Supported question patterns · Local SQLite database ·
            Read-only query execution
        </div>
        """,
        unsafe_allow_html=True,
    )

    footer()


def main():
    page = sidebar()

    if page == "Business Overview":
        overview()
    elif page == "Product Performance":
        product_performance()
    else:
        ask_your_data()


if __name__ == "__main__":
    main()

