import streamlit as st


def cleanup_temp_dir():
    if "temp_dir" in st.session_state:
        st.session_state.temp_dir.cleanup()
        del st.session_state.temp_dir
        st.write("Temporary directory has been deleted!")


def inject_js_to_cleanup():
    st.components.v1.html("""
    <script>
    window.addEventListener('beforeunload', (event) => {
        fetch('/cleanup_temp_dir');  // サーバーに削除リクエストを送信
    });
    </script>
    """, height=0)


def handle_cleanup_request():
    if st.experimental_get_query_params().get("cleanup_temp_dir"):
        cleanup_temp_dir()

