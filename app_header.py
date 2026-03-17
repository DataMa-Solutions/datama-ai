import streamlit as st


def render_app_header() -> None:
    st.markdown(
        """
        <style>
        .datama-header {
          display: flex;
          align-items: center;
          gap: 10px;
          margin: 0.4rem 0 0.2rem 0;
        }
        .datama-header__title {
          font-size: 2.25rem;
          line-height: 1.2;
          font-weight: 700;
          margin: 0;
        }
        .datama-help__icon {
          display: inline-flex;
          align-items: center;
          justify-content: center;
          width: 22px;
          height: 22px;
          color: rgba(49, 51, 63, 0.7);
          cursor: help;
          user-select: none;
          transform: translateY(2px);
        }
        .datama-help__icon:hover {
          color: rgba(49, 51, 63, 1);
        }
        .datama-help__tooltip {
          position: absolute;
          left: 0;
          top: 28px;
          width: min(520px, 86vw);
          padding: 12px 14px;
          border-radius: 12px;
          background: white;
          border: 1px solid rgba(49, 51, 63, 0.14);
          box-shadow: 0 10px 30px rgba(0, 0, 0, 0.12);
          display: none;
          z-index: 9999;
        }
        .datama-help__container {
          position: relative;
          display: inline-flex;
        }
        .datama-help__container::after {
          content: "";
          position: absolute;
          left: -12px;
          right: -12px;
          top: 18px;
          height: 18px;
        }
        .datama-help__container:hover .datama-help__tooltip {
          display: block;
        }
        .datama-help__tooltip p {
          margin: 0 0 10px 0;
          font-size: 0.9rem;
          line-height: 1.35rem;
        }
        .datama-help__tooltip p:last-child {
          margin-bottom: 0;
        }
        </style>

        <div class="datama-header">
          <h1 class="datama-header__title">Datama Compare AI Chat</h1>
          <div class="datama-help__container" aria-label="Learn more">
            <span class="datama-help__icon" aria-hidden="true">
              <svg width="22" height="22" viewBox="0 0 24 24" fill="none" aria-hidden="true">
                <path
                  d="M12 22C6.477 22 2 17.523 2 12S6.477 2 12 2s10 4.477 10 10-4.477 10-10 10Z"
                  stroke="currentColor"
                  stroke-width="1.8"
                />
                <path
                  d="M12 10.75v6"
                  stroke="currentColor"
                  stroke-width="1.8"
                  stroke-linecap="round"
                />
                <path
                  d="M12 7.25h.01"
                  stroke="currentColor"
                  stroke-width="2.6"
                  stroke-linecap="round"
                />
              </svg>
            </span>
            <div class="datama-help__tooltip" role="tooltip">
              <p>This app is intended to demo the usage of Datama AI kit in a simplified AI chat.</p>
              <p>
                It brings Datama
                <a href="https://datama.io/" target="_blank" rel="noopener noreferrer">analytics capabilities</a>
                in a standard "talk to my data" chat bot, powered by any LLM.
              </p>
              <p>
                Learn more
                <a href="https://github.com/DataMa-Solutions/datama-ai" target="_blank" rel="noopener noreferrer">on GitHub</a>.
              </p>
            </div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
