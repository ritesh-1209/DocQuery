import streamlit as st

class ThemeManager:
    def __init__(self):
        self.themes = {
            'light': {
                'background_color': '#FFFFFF',
                'text_color': '#000000',
                'primary_color': '#FF6B6B',
                'secondary_color': '#4ECDC4'
            },
            'dark': {
                'background_color': '#0E1117',
                'text_color': '#FFFFFF',
                'primary_color': '#FF6B6B',
                'secondary_color': '#4ECDC4'
            }
        }
    
    def apply_theme(self, theme_name: str):
        """Apply the selected theme using custom CSS"""
        if theme_name not in self.themes:
            theme_name = 'light'
        
        theme = self.themes[theme_name]
        
        # Enhanced CSS for better theming
        css = f"""
        <style>
        /* Root app styling */
        .stApp {{
            background-color: {theme['background_color']} !important;
            color: {theme['text_color']} !important;
        }}
        
        /* Sidebar styling */
        .css-1d391kg {{
            background-color: {theme['background_color']} !important;
        }}
        
        /* Main content area */
        .main .block-container {{
            background-color: {theme['background_color']} !important;
            color: {theme['text_color']} !important;
        }}
        
        /* Headers and text */
        .main-header, h1, h2, h3, h4, h5, h6 {{
            color: {theme['text_color']} !important;
        }}
        
        /* Buttons */
        .stButton > button {{
            border-radius: 8px !important;
            border: 1px solid {theme['primary_color']} !important;
            color: {theme['text_color']} !important;
            background-color: transparent !important;
        }}
        
        .stButton > button:hover {{
            background-color: {theme['primary_color']} !important;
            color: white !important;
        }}
        
        /* Primary buttons */
        .stButton > button[kind="primary"] {{
            background-color: {theme['primary_color']} !important;
            color: white !important;
        }}
        
        /* Text inputs */
        .stTextInput > div > div > input {{
            background-color: {theme['background_color']} !important;
            color: {theme['text_color']} !important;
            border-color: {theme['secondary_color']} !important;
        }}
        
        /* Select boxes */
        .stSelectbox > div > div > select {{
            background-color: {theme['background_color']} !important;
            color: {theme['text_color']} !important;
        }}
        
        /* File uploader */
        .stFileUploader > div {{
            background-color: {theme['background_color']} !important;
            border: 2px dashed {theme['secondary_color']} !important;
            border-radius: 10px !important;
        }}
        
        /* Chat messages */
        .stChatMessage {{
            background-color: {theme['background_color']} !important;
            color: {theme['text_color']} !important;
        }}
        
        /* Expanders */
        .streamlit-expanderHeader {{
            background-color: {theme['background_color']} !important;
            color: {theme['text_color']} !important;
        }}
        
        /* Metrics */
        .metric-container > div {{
            background-color: {theme['background_color']} !important;
            color: {theme['text_color']} !important;
        }}
        
        /* Sidebar elements */
        .css-1lcbmhc, .css-1v0mbdj {{
            background-color: {theme['background_color']} !important;
        }}
        
        /* Custom scrollbar */
        ::-webkit-scrollbar {{
            width: 8px;
        }}
        
        ::-webkit-scrollbar-track {{
            background: {theme['background_color']};
        }}
        
        ::-webkit-scrollbar-thumb {{
            background: {theme['secondary_color']};
            border-radius: 4px;
        }}
        
        ::-webkit-scrollbar-thumb:hover {{
            background: {theme['primary_color']};
        }}
        </style>
        """
        
        st.markdown(css, unsafe_allow_html=True)
    
    def get_theme_icon(self, current_theme: str) -> str:
        """Get the appropriate icon for theme toggle"""
        return "🌙" if current_theme == 'light' else "☀️"
    
    def create_themed_container(self, content: str, container_type: str = "default") -> str:
        """Create a themed container with custom styling"""
        class_name = f"{container_type}-container"
        return f'<div class="{class_name}">{content}</div>'
