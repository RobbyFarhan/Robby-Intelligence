import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import google.generativeai as genai
import io
import requests
import base64
import plotly.io as pio

# --- KONFIGURASI HALAMAN & GAYA ---
st.set_page_config(
    page_title="Media Intelligence Dashboard",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="collapsed" # UI Simplicity: Default collapsed for cleaner initial view
)

# --- FUNGSI UTAMA & LOGIKA ---

def configure_gemini_api():
    """
    Mengkonfigurasi API Gemini menggunakan kunci API.
    Dalam aplikasi produksi, gunakan st.secrets.
    """
    api_key = "AIzaSyC0VUu6xTFIwH3aP2R7tbhyu4O8m1ICxn4" # Replace with st.secrets["GEMINI_API_KEY"] in production
    if not api_key:
        st.warning("API Key Gemini tidak ditemukan. Beberapa fitur AI mungkin tidak berfungsi.")
        return False
    try:
        genai.configure(api_key=api_key)
        return True
    except Exception as e:
        st.error(f"Gagal mengkonfigurasi Gemini API: {e}. Pastikan API Key valid.")
        return False

def get_ai_insight(prompt, model_name='gemini-2.0-flash'):
    """
    Memanggil API GenAI untuk menghasilkan wawasan berdasarkan prompt dan model.
    """
    if not configure_gemini_api():
        return "Gagal membuat wawasan: API tidak terkonfigurasi."
    try:
        model = genai.GenerativeModel(model_name)
        response = model.generate_content(prompt)
        if response.candidates and response.candidates[0].content.parts:
            return response.candidates[0].content.parts[0].text
        else:
            st.error(f"Model {model_name} tidak menghasilkan teks yang valid.")
            return "Gagal membuat wawasan."
    except Exception as e:
        st.error(f"Error saat memanggil model {model_name}: {e}.")
        return "Gagal membuat wawasan: Terjadi masalah koneksi atau API."

def generate_html_report(campaign_summary, post_idea, anomaly_insight, chart_insights, chart_figures_dict, charts_to_display_info):
    """
    Membuat laporan HTML dari wawasan dan grafik yang dihasilkan AI.
    """
    current_date = pd.Timestamp.now().strftime("%d-%m-%Y %H:%M")

    anomaly_section_html = ""
    if anomaly_insight and anomaly_insight.strip() and anomaly_insight != "Belum ada wawasan yang dibuat.":
        anomaly_section_html = f"""
        <div class="section">
            <h2>3. Wawasan Anomali</h2>
            <div class="insight-box">{anomaly_insight}</div>
        </div>
        """
    
    chart_figures_html_sections = ""
    if chart_figures_dict:
        for chart_info in charts_to_display_info:
            chart_key = chart_info["key"]
            chart_title = chart_info["title"]
            fig = chart_figures_dict.get(chart_key)
            
            insights_for_chart = chart_insights.get(chart_key, {})
            insights_html = ""
            for style, text in insights_for_chart.items():
                if text:
                    insights_html += f"""
                    <h4>Wawasan AI (Gaya: {style}):</h4>
                    <div class="insight-box">{text}</div>
                    """

            if fig:
                try:
                    fig_for_export = go.Figure(fig)
                    # Ensure background is white for export
                    fig_for_export.update_layout(paper_bgcolor='#FFFFFF', plot_bgcolor='#FFFFFF', font_color='#333333')
                    img_bytes = pio.to_image(fig_for_export, format="png", width=900, height=550, scale=1.5)
                    img_base64 = base64.b64encode(img_bytes).decode('utf-8')
                    chart_figures_html_sections += f"""
                    <div class="insight-sub-section">
                        <h3>{chart_title}</h3>
                        <img src="data:image/png;base64,{img_base64}" alt="{chart_title}" style="max-width: 100%; height: auto; display: block; margin: 10px auto; border: 1px solid #ddd; border-radius: 5px;">
                        {insights_html}
                    </div>
                    """
                except Exception as e:
                    chart_figures_html_sections += f"<p>Gagal menyertakan grafik {chart_title} (Error: {e}).</p>"
            elif insights_for_chart:
                chart_figures_html_sections += f"""
                <div class="insight-sub-section">
                    <h3>{chart_title}</h3>
                    <p>Tidak ada grafik yang tersedia.</p>
                    {insights_html}
                </div>
                """
    else:
        chart_figures_html_sections = "<p>Belum ada wawasan atau grafik yang dibuat.</p>"

    html_content = f"""
    <!DOCTYPE html><html><head><title>Laporan Media Intelligence Dashboard</title><meta charset="UTF-8">
    <style>
        body {{ font-family: 'Inter', sans-serif; line-height: 1.6; color: #333; margin: 20px; background-color: #f4f4f4; }}
        h1, h2, h3, h4 {{ color: #2c3e50; margin-top: 1.5em; margin-bottom: 0.5em; }}
        .section {{ background-color: #fff; padding: 15px; margin-bottom: 15px; border-radius: 8px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }}
        .insight-sub-section {{ margin-top: 1em; padding-left: 15px; border-left: 3px solid #eee; }}
        .insight-box {{ background-color: #e9ecef; padding: 10px; border-radius: 5px; font-size: 0.9em; white-space: pre-wrap; word-wrap: break-word; }}
    </style></head><body>
    <h1>Laporan Media Intelligence Dashboard</h1><p>Tanggal Laporan: {current_date}</p>
    <div class="section"><h2>1. Ringkasan Strategi Kampanye</h2><div class="insight-box">{campaign_summary or "Belum ada ringkasan."}</div></div>
    <div class="section"><h2>2. Ide Konten AI</h2><div class="insight-box">{post_idea or "Belum ada ide."}</div></div>
    {anomaly_section_html}
    <div class="section"><h2>4. Wawasan Grafik</h2>{chart_figures_html_sections}</div>
    </body></html>
    """
    return html_content.encode('utf-8')

# PERUBAHAN FONT & UI HANYA DI DALAM FUNGSI INI
def load_css():
    """Menyuntikkan CSS kustom dengan gradien hijau."""
    st.markdown("""
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@700;800&family=Inter:wght@400;500;600;700&display=swap'); /* Add Inter font */
            body { background-color: #042f2e !important; } /* Ensure full body background */
            .stApp { 
                background-image: radial-gradient(at top left, #104e4a, #042f2e, black); 
                color: #e5e7eb; 
                font-family: 'Inter', sans-serif; /* UI Simplicity: Use Inter for general text */
            }
            .main-header { 
                font-family: 'Plus Jakarta Sans', sans-serif;
                text-align: center; 
                margin-bottom: 2rem; 
            }
            .main-header h1 { 
                background: -webkit-linear-gradient(45deg, #6EE7B7, #10B981); 
                -webkit-background-clip: text; 
                -webkit-text-fill-color: transparent; 
                font-size: 2.75rem; 
                font-weight: 800; /* UI Simplicity: Ensure bold for main header */
            }
            .main-header p { color: #9ca3af; font-size: 1.1rem; }
            /* UI Simplicity: Combined common card styles for consistency */
            .chart-container, .insight-hub, .anomaly-card, .uploaded-file-info, .st-emotion-cache-1r6dm7m { /* Targets st.container, st.columns, etc */
                border: 1px solid #134E4A;
                background-color: rgba(16, 56, 48, 0.7);
                backdrop-filter: blur(15px); 
                border-radius: 1rem; 
                padding: 1.5rem; 
                margin-bottom: 2rem; 
                box-shadow: 0 4px 30px rgba(0, 0, 0, 0.2); 
                box-sizing: border-box; 
            }
            .anomaly-card { 
                border: 2px solid #f59e0b;
                background-color: rgba(245, 158, 11, 0.1); 
            }
            .insight-box { 
                background-color: rgba(4, 47, 46, 0.75);
                border: 1px solid #064E3B;
                border-radius: 0.5rem; 
                padding: 1rem; 
                margin-top: 1rem; 
                min-height: 150px; 
                white-space: pre-wrap; 
                word-wrap: break-word; 
                font-size: 0.9rem; 
                color: #e5e7eb; /* UI Simplicity: Ensure insight text is readable */
            }
            .chart-container h3, .insight-hub h3, .anomaly-card h3, .insight-hub h4, .uploaded-file-info h3 { 
                color: #34D399; /* UI Simplicity: Consistent heading color */
                margin-top: 0; 
                margin-bottom: 1rem; 
                display: flex; 
                align-items: center; 
                gap: 0.5rem; 
                font-weight: 600; 
            }
            .uploaded-file-info { color: #e5e7eb; }
            .uploaded-file-info p { margin-bottom: 0.5rem; }

            /* Streamlit specific overrides for better UI Simplicity */
            .stFileUploader > div {
                border: 2px dashed #064E3B;
                border-radius: 1rem;
                padding: 2rem;
                background-color: rgba(16, 56, 48, 0.7);
                margin-top: 1rem;
            }
            .stFileUploader label { color: #34D399; font-size: 1.1rem; font-weight: 600; }
            .stButton > button {
                border-radius: 0.5rem;
                padding: 0.75rem 1rem;
                font-weight: bold;
            }
            .stButton > button:hover {
                opacity: 0.8;
                transition: opacity 0.2s ease-in-out;
            }
            .stSelectbox > div > div > div { /* Target the selectbox dropdown */
                background-color: rgba(4, 47, 46, 0.9); /* Darker background for dropdown */
                color: #e5e7eb;
                border: 1px solid #064E3B;
            }
            .stSelectbox > label { color: #34D399; font-weight: 600; }
            .stExpander > div > div {
                background-color: rgba(16, 56, 48, 0.7); /* Match card background */
                border: 1px solid #134E4A;
                border-radius: 1rem;
                padding: 1.5rem;
                margin-bottom: 2rem;
            }
            .stExpander > div > div > div > p {
                color: #34D399; /* Expander header color */
                font-weight: 600;
                font-size: 1.1rem;
            }
            .stExpander div[data-testid="stExpanderForm"] { /* Inner content of expander */
                padding-top: 0.5rem;
            }
            .st-emotion-cache-10o5h6q { /* Targets text input */
                background-color: rgba(4, 47, 46, 0.75);
                border: 1px solid #064E3B;
                border-radius: 0.5rem;
                color: #e5e7eb;
            }
            .st-emotion-cache-10o5h6q input {
                color: #e5e7eb;
            }
            .st-emotion-cache-10o5h6q label {
                color: #34D399;
                font-weight: 600;
            }
        </style>
    """, unsafe_allow_html=True)

@st.cache_data
def parse_csv(uploaded_file):
    """Membaca dan membersihkan file CSV."""
    try:
        df = pd.read_csv(uploaded_file)
        if 'Media_Type' in df.columns:
            df.rename(columns={'Media_Type': 'Media Type'}, inplace=True)
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
        df['Engagements'] = pd.to_numeric(df['Engagements'], errors='coerce')
        df.dropna(subset=['Date', 'Engagements'], inplace=True)
        df['Engagements'] = df['Engagements'].astype(int)
        for col in ['Platform', 'Sentiment', 'Media Type', 'Location', 'Headline']:
            if col not in df.columns:
                df[col] = 'N/A'
        df[['Platform', 'Sentiment', 'Media Type', 'Location', 'Headline']] = df[['Platform', 'Sentiment', 'Media Type', 'Location', 'Headline']].fillna('N/A')
        return df
    except Exception as e:
        st.error(f"Gagal memproses file CSV: {e}")
        return None

@st.dialog("AI Media Consultant")
def run_consultant_chat(df_summary):
    """Menjalankan antarmuka chat di dalam st.dialog."""
    st.markdown("Tanyakan apa pun tentang data media Anda atau strategi umum.")

    if "consultant_messages" not in st.session_state:
        st.session_state.consultant_messages = [{"role": "assistant", "content": "Halo! Saya adalah konsultan media AI Anda. Apa yang bisa saya bantu analisis hari ini?"}]

    for msg in st.session_state.consultant_messages:
        st.chat_message(msg["role"]).write(msg["content"])

    if prompt := st.chat_input("Ketik pertanyaan Anda..."):
        st.session_state.consultant_messages.append({"role": "user", "content": prompt})
        st.chat_message("user").write(prompt)

        full_prompt = f"""
        Anda adalah seorang konsultan media AI yang ahli, ramah, dan profesional. 
        Tugas Anda adalah menjawab pertanyaan pengguna terkait analisis media, strategi kampanye, atau interpretasi data.
        Gunakan ringkasan data berikut sebagai konteks jika relevan: 
        ---
        {df_summary}
        ---
        Riwayat percakapan sejauh ini: {st.session_state.consultant_messages}
        ---
        Jawab pertanyaan pengguna berikut: "{prompt}"
        """
        
        with st.chat_message("assistant"):
            with st.spinner("Memikirkan jawaban..."):
                response = get_ai_insight(full_prompt)
                st.session_state.consultant_messages.append({"role": "assistant", "content": response})
                st.write(response)

# --- UI STREAMLIT ---
load_css()
api_configured = configure_gemini_api()

st.markdown("<div class='main-header'><h1>Media Intelligence Dashboard</h1><p>Nouval Media Consultant</p></div>", unsafe_allow_html=True)

# Inisialisasi State
for key in ['data', 'chart_insights', 'campaign_summary', 'post_idea', 'anomaly_insight', 'chart_figures', 'last_uploaded_file_name', 'last_uploaded_file_size', 'show_analysis', 'last_filter_state']:
    if key not in st.session_state:
        st.session_state[key] = None if key not in ['chart_insights', 'chart_figures'] else {}
        if key == 'show_analysis': st.session_state[key] = False

# Tampilan Unggah File
if st.session_state.data is None: 
    # UI Simplicity: Centralize file uploader
    c1, c2, c3 = st.columns([1,2,1]) 
    with c2: # Use middle column for centered Uploader
        with st.container(border=False): # Removed border for cleaner look, let custom CSS handle it
            st.markdown("### ☁️ Unggah File CSV Anda")
            uploaded_file = st.file_uploader("Pastikan file memiliki kolom 'Date', 'Engagements', 'Sentiment', 'Platform', 'Media Type', 'Location', dll.", type="csv", label_visibility="collapsed")
            if uploaded_file:
                st.session_state.data = parse_csv(uploaded_file)
                if st.session_state.data is not None:
                    st.session_state.last_uploaded_file_name = uploaded_file.name
                    st.session_state.last_uploaded_file_size = uploaded_file.size
                    st.session_state.show_analysis = False
                    st.rerun()

# Tampilan Dasbor Utama
if st.session_state.data is not None:
    df = st.session_state.data
    st.markdown(f"""<div class="uploaded-file-info"><h3>📂 File Berhasil Terunggah! ✅️</h3><p><strong>Nama File:</strong> {st.session_state.last_uploaded_file_name}</p></div>""", unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Hapus File & Reset", key="clear_file_btn", use_container_width=True, type="secondary"): # Made secondary for distinction
            for key in list(st.session_state.keys()): del st.session_state[key]
            st.rerun()
    with col2:
        if st.button("💬 Buka AI Consultant", key="open_chat_btn", use_container_width=True, type="primary"): # Made primary as it's a key feature
            df_summary_for_chat = df.describe(include='all').to_string()
            run_consultant_chat(df_summary_for_chat)


    if not st.session_state.show_analysis:
        st.markdown("---") # UI Simplicity: Add a separator
        if st.button("▶️ Lihat Hasil Analisis Datamu!", key="show_analysis_btn", use_container_width=True, type="primary"):
            st.session_state.show_analysis = True
            st.rerun()

    if st.session_state.show_analysis:
        st.markdown("---") # UI Simplicity: Add a separator after previous buttons
        with st.expander("⚙️ Filter Data & Opsi Tampilan", expanded=True):
            def get_multiselect(label, options):
                all_option = f"Pilih Semua {label}"
                selection = st.multiselect(label, [all_option] + options)
                if all_option in selection: return options
                return selection

            min_date, max_date = df['Date'].min().date(), df['Date'].max().date()
            fc1, fc2, fc3 = st.columns([2, 2, 3])
            with fc1:
                platform = get_multiselect("Platform", sorted(df['Platform'].unique()))
                media_type = get_multiselect("Media Type", sorted(df['Media Type'].unique()))
            with fc2:
                sentiment = get_multiselect("Sentiment", sorted(df['Sentiment'].unique()))
                location = get_multiselect("Location", sorted(df['Location'].unique()))
            with fc3:
                date_range = st.date_input("Rentang Tanggal", (min_date, max_date), min_date, max_date, format="DD/MM/YYYY")
                start_date, end_date = date_range if len(date_range) == 2 else (min_date, max_date)

        # Filter dan proses data
        query = "(Date >= @start_date) & (Date <= @end_date)"
        params = {'start_date': pd.to_datetime(start_date), 'end_date': pd.to_datetime(end_date)}
        if platform: query += " & Platform in @platform"; params['platform'] = platform
        if sentiment: query += " & Sentiment in @sentiment"; params['sentiment'] = sentiment
        if media_type: query += " & `Media Type` in @media_type"; params['media_type'] = media_type
        if location: query += " & Location in @location"; params['location'] = location
        filtered_df = df.query(query, local_dict=params)

        # Tampilan Grafik & AI
        charts_to_display = [
            {"key": "sentiment", "title": "Analisis Sentimen"},
            {"key": "trend", "title": "Tren Keterlibatan"},
            {"key": "platform", "title": "Keterlibatan per Platform"},
            {"key": "mediaType", "title": "Distribusi Jenis Media"},
            {"key": "location", "title": "5 Lokasi Teratas"}
        ]
        
        # UI Simplicity: Use columns for chart display
        chart_cols = st.columns(2) 
        
        def get_chart_prompt(key, data_json, answer_style):
            prompts = {"sentiment": "distribusi sentimen", "trend": "tren keterlibatan", "platform": "keterlibatan per platform", "mediaType": "distribusi jenis media", "location": "keterlibatan per lokasi"}
            
            personas = {
                "gemini-2.0-flash": "Anda adalah seorang analis media yang sangat kritis dan skeptis. Fokus pada potensi risiko, kelemahan data, dan anomali yang tidak terduga. Berikan 3 poin observasi tajam.",
                "Mistral 7B Instruct": "Anda adalah seorang ahli strategi branding yang kreatif dan visioner. Lihat data ini sebagai kanvas. Berikan 3 ide kampanye atau konten yang inovatif dan out-of-the-box berdasarkan tren yang ada.",
                "llama-3.3-8b-instruct": "Anda adalah seorang pakar data yang sangat kuantitatif dan to-the-point. Berikan 3 kesimpulan actionable yang didukung langsung oleh angka-angka dalam data. Sebutkan angka spesifik jika memungkinkan."
            }
            
            persona = personas.get(answer_style, "Anda adalah asisten AI. Berikan 3 wawasan dari data berikut.")
            
            return f"{persona} Analisis data mengenai {prompts.get(key, 'data')}: {data_json}. Sajikan wawasan dalam format daftar bernomor yang jelas."

        for i, chart in enumerate(charts_to_display):
            with chart_cols[i % 2]: # Place charts in a 2-column layout
                with st.container(border=True):
                    st.markdown(f'<h3>📊 {chart["title"]}</h3>', unsafe_allow_html=True) # UI Simplicity: Add icon to chart titles
                    fig, data_for_prompt = None, None
                    if not filtered_df.empty:
                        try:
                            if chart["key"] == "sentiment": data = filtered_df['Sentiment'].value_counts().reset_index(); fig = px.pie(data, names='Sentiment', values='count')
                            elif chart["key"] == "trend": data = filtered_df.groupby(filtered_df['Date'].dt.date)['Engagements'].sum().reset_index(); fig = px.line(data, x='Date', y='Engagements')
                            elif chart["key"] == "platform": data = filtered_df.groupby('Platform')['Engagements'].sum().nlargest(10).reset_index(); fig = px.bar(data, x='Platform', y='Engagements', color='Platform')
                            elif chart["key"] == "mediaType": data = filtered_df['Media Type'].value_counts().reset_index(); fig = px.pie(data, names='Media Type', values='count', hole=.3)
                            elif chart["key"] == "location": data = filtered_df.groupby('Location')['Engagements'].sum().nlargest(5).reset_index(); fig = px.bar(data, y='Location', x='Engagements', orientation='h')
                            data_for_prompt = data.to_json(orient='records')
                        except Exception: pass
                    
                    if fig:
                        st.session_state.chart_figures[chart["key"]] = fig
                        fig.update_layout(
                            paper_bgcolor='rgba(0,0,0,0)', # UI Simplicity: Transparent background
                            plot_bgcolor='rgba(0,0,0,0)',  # UI Simplicity: Transparent plot area
                            font_color='#e5e7eb',          # UI Simplicity: Light font for dark theme
                            legend_title_text=''
                        )
                        st.plotly_chart(fig, use_container_width=True)
                    else: st.warning("Tidak ada data untuk ditampilkan dengan filter ini.")
                    
                    answer_styles = ["gemini-2.0-flash", "Mistral 7B Instruct", "llama-3.3-8b-instruct"]
                    selected_style = st.selectbox(
                        "Pilih Gaya Jawaban AI:",
                        answer_styles,
                        key=f"sel_{chart['key']}"
                    )

                    if st.button("✨ Generate Insight dengan AI", key=f"btn_{chart['key']}", use_container_width=True, type="primary"):
                        if data_for_prompt:
                            with st.spinner(f"Menganalisis {chart['title']} dengan gaya '{selected_style}'..."):
                                prompt = get_chart_prompt(chart['key'], data_for_prompt, selected_style)
                                
                                if chart['key'] not in st.session_state.chart_insights:
                                    st.session_state.chart_insights[chart['key']] = {}
                                
                                st.session_state.chart_insights[chart['key']][selected_style] = get_ai_insight(prompt)
                                st.rerun()
                    
                    chart_specific_insights = st.session_state.chart_insights.get(chart.get("key"), {})
                    insight_text = chart_specific_insights.get(selected_style, "Pilih model AI untuk menampilkan insight untukmu!.")
                    st.markdown(f'<div class="insight-box">{insight_text}</div>', unsafe_allow_html=True)

        # Wawasan Umum & Unduh
        st.markdown("---") # UI Simplicity: Separator
        with st.container(border=True):
            st.markdown("<h3>🧠 Insight Lanjutan </h3>", unsafe_allow_html=True) # UI Simplicity: Add icon
            c1, c2 = st.columns(2)
            with c1:
                st.markdown("<h4>📝 Ringkasan Strategi Kampanye Anda</h4>", unsafe_allow_html=True) # UI Simplicity: Add icon
                if st.button("Buat Ringkasan", use_container_width=True, type="primary"):
                    with st.spinner("Membuat ringkasan..."):
                        st.session_state.campaign_summary = get_ai_insight(f"Data: {filtered_df.describe().to_json()}. Buat ringkasan eksekutif dan 3 rekomendasi strategis.")
                st.info(st.session_state.campaign_summary or "Klik 'Buat Ringkasan' untuk mendapatkan rangkuman strategi kampanye berdasarkan data Anda.") # UI Simplicity: More informative placeholder
            with c2:
                st.markdown("<h4>💡 Buatkan Ide Konten</h4>", unsafe_allow_html=True) # UI Simplicity: Add icon
                if st.button("Buat Ide Postingan", use_container_width=True, type="primary"):
                    with st.spinner("Mencari ide..."):
                        best_platform = filtered_df.groupby('Platform')['Engagements'].sum().idxmax() if not filtered_df.empty else "N/A"
                        st.session_state.post_idea = get_ai_insight(f"Buat satu ide postingan untuk platform {best_platform}, termasuk visual & tagar.")
                st.info(st.session_state.post_idea or "Klik 'Buat Ide Postingan' untuk mendapatkan saran konten baru yang inovatif.") # UI Simplicity: More informative placeholder
        
        st.markdown("---") # UI Simplicity: Separator
        with st.container(border=True):
            st.markdown("<h3>📄 Unduh Laporan Analisis</h3>", unsafe_allow_html=True) # UI Simplicity: Add icon
            if st.download_button(
                "Unduh Laporan Lengkap (HTML)", 
                data=generate_html_report(st.session_state.campaign_summary, st.session_state.post_idea, st.session_state.anomaly_insight, st.session_state.chart_insights, st.session_state.chart_figures, charts_to_display), 
                file_name="Laporan_Media_Intelligence.html", 
                mime="text/html", 
                use_container_width=True,
                type="secondary" # UI Simplicity: Make download button secondary
            ):
                st.success("Laporan berhasil dibuat dan siap diunduh!")
