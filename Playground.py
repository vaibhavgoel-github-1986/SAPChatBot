import streamlit as st
from streamlit_ace import st_ace

st.title("💻 SAP ABAP Code Editor (Custom Theme)")

# Sample ABAP code
default_abap_code = """CLASS zcl_example DEFINITION PUBLIC FINAL CREATE PUBLIC.
  PUBLIC SECTION.\n
    METHODS: display IMPORTING iv_text TYPE string.
ENDCLASS.

CLASS zcl_example IMPLEMENTATION.
  METHOD display.
    WRITE: iv_text.
  ENDMETHOD.
ENDCLASS.
"""

# Define a custom theme for ABAP highlighting
custom_theme = """
    ace.define('ace/theme/custom_abap', ['require', 'exports', 'module', 'ace/lib/dom'], function(acequire, exports, module) {
        exports.isDark = false;
        exports.cssClass = 'ace-custom-abap';
        exports.cssText = ".ace-custom-abap .ace_keyword {color: #67b6ff !important; font-weight: bold;} " + 
                          ".ace-custom-abap .ace_comment {color: gray !important; font-style: italic;} " +
                          ".ace-custom-abap .ace_string {color: #A31515 !important;} " +
                          ".ace-custom-abap .ace_function {color: #795E26 !important;} " +
                          ".ace-custom-abap .ace_type {color: #267F99 !important;} ";

        var dom = acequire('ace/lib/dom');
        dom.importCssString(exports.cssText, exports.cssClass);
    });
"""

THEMES = [
    "ambiance", "chaos", "chrome", "clouds", "clouds_midnight", "cobalt", "crimson_editor", "dawn",
    "dracula", "dreamweaver", "eclipse", "github", "gob", "gruvbox", "idle_fingers", "iplastic",
    "katzenmilch", "kr_theme", "kuroir", "merbivore", "merbivore_soft", "mono_industrial", "monokai",
    "nord_dark", "pastel_on_dark", "solarized_dark", "solarized_light", "sqlserver", "terminal",
    "textmate", "tomorrow", "tomorrow_night", "tomorrow_night_blue", "tomorrow_night_bright",
    "tomorrow_night_eighties", "twilight", "vibrant_ink", "xcode"
]

# Set the theme to match `st.code()` style (closest theme is `xcode` or `github`)
theme = st.selectbox("Choose Theme", THEMES, index=0)


# Inject custom theme into Streamlit
st.markdown(f"<script>{custom_theme}</script>", unsafe_allow_html=True)

# Streamlit Ace Editor with Custom Theme
code = st_ace(
    value=default_abap_code,
    language="abap",
    theme= "crimson_editor", #"custom_abap",  # Pass the custom theme
    font_size=14,
    # tab_size=2,
    show_gutter=False,
    wrap=False,
    key="abap_editor",
    auto_update=True
)

    
# Display the updated code
st.subheader("Edited Code:")
st.code(code, language="abap")
