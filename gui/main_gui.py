import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
import subprocess
import threading
import os
import sys
import json
import re
import signal
import requests
import time
import collections
from PIL import Image
from tkinter import ttk
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.animation as animation
import customtkinter
if sys.platform == "win32":
    os.system("chcp 65001")


from logic.config import load_stored_output_dir, store_output_dir
from logic.downloader import smart_download as ytdlp_smart_download
from logic.downloader import is_youtube
from logic.downloader import download_gallery as gallery_download
from logic.downloader import kill_proc_tree

# PyInstaller 환경에서 리소스 파일 경로 처리
def resource_path(relative_path):
    """ PyInstaller 환경에서 리소스 파일 경로를 가져오는 함수 """
    try:
        # PyInstaller가 생성한 임시 폴더 경로
        base_path = sys._MEIPASS
    except Exception:
        # 일반 Python 환경에서는 현재 디렉토리 사용
        base_path = os.path.abspath(".")
    
    return os.path.join(base_path, relative_path)

# 설정 파일 경로 지정
CONFIG_STORE = resource_path("config.json")

CREATE_NO_WINDOW = 0x08000000
# 색상 정의
HACKER_GREEN = "#1fff1f"  # 기본 네온 그린 색상
HACKER_BG = "#0f0f0f"    # 기본 배경 색상
HACKER_DARK = "#1a1a1a"  # 어두운 배경 색상
HACKER_ACCENT = "#4dff4d" # 강조 색상
HACKER_RED = "#ff3333"    # 경고 및 취소 색상
HACKER_BLUE = "#33ffff"   # 정보 표시 색상
HACKER_YELLOW = "#ffff33" # 주의 색상
HACKER_PURPLE = "#ff33ff" # 특수 기능 색상
HACKER_ORANGE = "#ff9933" # 보조 강조 색상
HACKER_BORDER = "#2a2a2a" # 테두리 색상
TITLE_BAR_BG = "#1a1a1a"  # 타이틀바 배경 색상
TITLE_BAR_FG = "#999999"  # 타이틀바 텍스트 색상
TITLE_BAR_BUTTON_BG = "#333333"  # 타이틀바 버튼 배경 색상
TITLE_BAR_BUTTON_HOVER = "#4d4d4d"  # 타이틀바 버튼 호버 색상
TITLE_BAR_HEIGHT = 30  # 타이틀바 높이
placeholder_text = "파일이름 입력 (선택)"
DOWNLOAD_BTN_COLOR = "#ff1a1a"  # 다운로드 버튼 색상
DOWNLOAD_BTN_HOVER = "#ff4d4d"  # 다운로드 버튼 호버 색상

class GalleryDLGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("KEMYOUHIT DOWNLOADER")
        self.root.geometry("800x900")
        self.root.configure(bg=HACKER_BG)
        self.root.resizable(False, False)
        
        # DPI 인식 설정
        if sys.platform == "win32":
            try:
                from ctypes import windll
                windll.shcore.SetProcessDpiAwareness(1)
            except:
                pass

        # 초기화
        self.processes = []
        self.stored_dir = load_stored_output_dir()
        self._cancel_requested = False
        
        # URL 세트 초기화
        self.url_sets = []  # 케모노파티 URL 세트
        self.yt_url_sets = []  # 유튜브 URL 세트
        self.hitomi_url_sets = []  # 히토미 URL 세트

        # 메인 컨테이너 생성
        self.container = tk.Frame(self.root, bg=HACKER_BG)
        self.container.pack(fill="both", expand=True)

        # 상단 탭 버튼 프레임
        self.tab_button_frame = tk.Frame(self.container, bg=HACKER_BG)
        self.tab_button_frame.pack(fill="x", padx=2, pady=2)

        # 컨텐츠 프레임 생성
        self.content_frame = tk.Frame(self.container, bg=HACKER_BG)
        self.content_frame.pack(fill="both", expand=True, padx=2, pady=2)

        # 각 탭의 프레임 생성
        self.gallery_dl_frame = tk.Frame(self.content_frame, bg=HACKER_BG)
        self.ytdlp_frame = tk.Frame(self.content_frame, bg=HACKER_BG)
        self.hitomi_frame = tk.Frame(self.content_frame, bg=HACKER_BG)
        self.help_frame = tk.Frame(self.content_frame, bg=HACKER_BG)

        # 탭 버튼 생성
        self.create_tab_buttons()

        # 초기 탭 표시
        self.show_tab(self.gallery_dl_frame)

        self.init_gallery_dl_ui()
        self.init_ytdlp_ui()
        self.init_hitomi_ui()
        self.init_help_tab()

        # 새 창 열기 버튼
        new_window_btn = tk.Button(self.tab_button_frame, text="[ + 추가 다운로더 ]", 
                             font=("Malgun Gothic", 12, "bold"),
                             bg=HACKER_BG, fg=HACKER_GREEN,
                             activebackground=HACKER_GREEN,
                             activeforeground=HACKER_BG,
                             relief="flat",
                             command=self.open_new_window,
                             cursor="hand2")
        new_window_btn.pack(side="right", padx=5)

        # Config 버튼
        config_btn = tk.Button(self.tab_button_frame, text="[ ⚙ CONFIG ]", 
                             font=("Malgun Gothic", 12, "bold"),
                             bg=HACKER_BG, fg=HACKER_GREEN,
                             activebackground=HACKER_GREEN,
                             activeforeground=HACKER_BG,
                             relief="flat",
                             command=self.open_or_create_config,
                             cursor="hand2")
        config_btn.pack(side="right", padx=5)

        # 최소 창 크기 설정
        self.root.minsize(700, 900)
        
        # 창 테두리 설정
        self.container.configure(highlightbackground=HACKER_BORDER, highlightthickness=1)
        
        # 윈도우 종료 시 이벤트 처리
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def create_tab_buttons(self):
        # 탭 버튼 스타일
        button_style = {
            "font": ("Malgun Gothic", 12, "bold"),
            "relief": "flat",
            "borderwidth": 0,
            "padx": 20,
            "pady": 5,
            "cursor": "hand2"
        }

        # KEMONOPARTY 버튼
        self.gallery_btn = tk.Button(self.tab_button_frame,
                                   text="KEMONOPARTY",
                                   bg=HACKER_GREEN,
                                   fg=HACKER_BG,
                                   command=lambda: self.show_tab(self.gallery_dl_frame),
                                   **button_style)
        self.gallery_btn.pack(side="left", padx=2)

        # YOUTUBE 버튼
        self.ytdlp_btn = tk.Button(self.tab_button_frame,
                                 text="YOUTUBE",
                                 bg=HACKER_BG,
                                 fg=HACKER_GREEN,
                                 command=lambda: self.show_tab(self.ytdlp_frame),
                                 **button_style)
        self.ytdlp_btn.pack(side="left", padx=2)

        # HITOMI 버튼
        self.hitomi_btn = tk.Button(self.tab_button_frame,
                                  text="HITOMI",
                                  bg=HACKER_BG,
                                  fg=HACKER_GREEN,
                                  command=lambda: self.show_tab(self.hitomi_frame),
                                  **button_style)
        self.hitomi_btn.pack(side="left", padx=2)

        # 도움말 버튼
        self.help_btn = tk.Button(self.tab_button_frame,
                                text="도움말",
                                bg=HACKER_BG,
                                fg=HACKER_GREEN,
                                command=lambda: self.show_tab(self.help_frame),
                                **button_style)
        self.help_btn.pack(side="left", padx=2)

    def show_tab(self, tab_frame):
        # 모든 프레임 숨기기
        for frame in [self.gallery_dl_frame, self.ytdlp_frame, self.hitomi_frame, self.help_frame]:
            frame.pack_forget()
        
        # 모든 버튼 비활성화 스타일로 변경
        for btn in [self.gallery_btn, self.ytdlp_btn, self.hitomi_btn, self.help_btn]:
            btn.configure(bg=HACKER_BG, fg=HACKER_GREEN)
        
        # 선택된 탭 표시
        tab_frame.pack(fill="both", expand=True)
        
        # 선택된 버튼 활성화 스타일로 변경
        if tab_frame == self.gallery_dl_frame:
            self.gallery_btn.configure(bg=HACKER_GREEN, fg=HACKER_BG)
        elif tab_frame == self.ytdlp_frame:
            self.ytdlp_btn.configure(bg=HACKER_GREEN, fg=HACKER_BG)
        elif tab_frame == self.hitomi_frame:
            self.hitomi_btn.configure(bg=HACKER_GREEN, fg=HACKER_BG)
        elif tab_frame == self.help_frame:
            self.help_btn.configure(bg=HACKER_GREEN, fg=HACKER_BG)

    def center_window(self):
        """윈도우를 화면 중앙에 위치시킴"""
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')

    def on_closing(self):
        """프로그램 종료 처리"""
        try:
            # 실행 중인 모든 프로세스 종료
            for proc in self.processes:
                try:
                    if os.name == "nt":
                        kill_proc_tree(proc.pid)
                    else:
                        proc.terminate()
                except:
                    pass
            
            # 윈도우 종료
            if self.root:
                self.root.quit()
                self.root.destroy()
            
            # 프로세스 완전 종료
            if hasattr(sys, 'exit'):
                sys.exit(0)
            else:
                os._exit(0)
        except:
            # 강제 종료
            os._exit(1)

    def init_gallery_dl_ui(self):
        """gallery-dl 다운로더 탭 UI 초기화"""
        main_container = tk.Frame(self.gallery_dl_frame, bg=HACKER_BG)
        main_container.pack(padx=20, pady=20, fill="both", expand=True)
        
        # Title
        title_frame = tk.Frame(main_container, bg=HACKER_BG)
        title_frame.pack(fill="x", pady=(0, 15))
        
        title_label = self.create_common_label(title_frame, "[ KEMONOPARTY 다운로더 ]", is_title=True)
        title_label.pack(side="left")
        
        # File extension filters
        filters_section = tk.Frame(main_container, bg=HACKER_BG)
        filters_section.pack(fill="x", pady=(0, 15))
        
        filters_label = self.create_common_label(filters_section, "[ 확장자 선택(미선택시 전체 다운) ]")
        filters_label.pack(anchor="w", pady=(0, 5))
        
        filters_frame = tk.Frame(filters_section, bg=HACKER_BG)
        filters_frame.pack(fill="x")
        
        self.filter_vars = {ext: tk.BooleanVar() for ext in ["zip", "7z", "mp4", "jpeg", "png", "gif", "rar", "psd"]}
        
        for ext, var in self.filter_vars.items():
            cb = tk.Checkbutton(
                filters_frame,
                text=f"[{ext}]",
                variable=var,
                font=("Malgun Gothic", 12),
                bg=HACKER_BG,
                fg=HACKER_GREEN,
                selectcolor=HACKER_DARK,
                activebackground=HACKER_BG,
                activeforeground=HACKER_GREEN,
                cursor="hand2"
            )
            cb.pack(side="left", padx=(0, 15))
        
        # URL input section with scrollable container
        url_section = tk.Frame(main_container, bg=HACKER_BG)
        url_section.pack(fill="x", pady=(0, 15))
        
        url_label = self.create_common_label(url_section, "[ URL 입력 ]")
        url_label.pack(anchor="w", pady=(0, 5))
        
        # Create a frame to hold the canvas and scrollbar
        url_scroll_frame = tk.Frame(url_section, bg=HACKER_BG)
        url_scroll_frame.pack(fill="x", expand=True)
        url_scroll_frame.configure(height=80)  # 높이 설정
        url_scroll_frame.pack_propagate(False)  # 크기 고정
        
        # Create canvas and scrollbar
        self.url_canvas = tk.Canvas(url_scroll_frame, bg=HACKER_BG, highlightthickness=0)
        url_scrollbar = ttk.Scrollbar(url_scroll_frame, orient="vertical", command=self.url_canvas.yview)
        
        # Create a frame inside canvas to hold URL entries
        self.url_container = tk.Frame(self.url_canvas, bg=HACKER_BG)
        self.url_container.bind("<Configure>", lambda e: self.url_canvas.configure(scrollregion=self.url_canvas.bbox("all")))
        
        # Add the URL container frame to the canvas
        self.url_canvas.create_window((0, 0), window=self.url_container, anchor="nw", width=740)  # 고정된 너비 설정
        self.url_canvas.configure(yscrollcommand=url_scrollbar.set)
        
        # Pack canvas and scrollbar
        self.url_canvas.pack(side="left", fill="both", expand=True)
        url_scrollbar.pack(side="right", fill="y")
        
        # URL control buttons
        url_controls = tk.Frame(url_section, bg=HACKER_BG)
        url_controls.pack(fill="x", pady=(10, 0))
        
        self.add_url_btn = self.create_common_button(url_controls, "[ + ADD URL ]", self.add_url_field)
        self.add_url_btn.pack(side="left", padx=(0, 10))
        
        self.remove_url_btn = self.create_common_button(url_controls, "[ - REMOVE URL ]", self.remove_url_field)
        self.remove_url_btn.pack(side="left", padx=(0, 10))
        
        self.clear_url_btn = self.create_common_button(url_controls, "[ URL 초기화 ]", self.clear_all_urls)
        self.clear_url_btn.pack(side="left")
        
        # Output directory section
        output_section = tk.Frame(main_container, bg=HACKER_BG)
        output_section.pack(fill="x", pady=(0, 15))
        
        output_label = self.create_common_label(output_section, "[ 저장위치 ]")
        output_label.pack(anchor="w", pady=(0, 5))
        
        output_frame = tk.Frame(output_section, bg=HACKER_BG)
        output_frame.pack(fill="x")
        
        self.output_dir_var = tk.StringVar(value=self.stored_dir or os.getcwd())
        self.output_entry = self.create_common_entry(output_frame, "", width=50)
        self.output_entry.config(textvariable=self.output_dir_var)
        self.output_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        
        browse_btn = self.create_common_button(output_frame, "[ BROWSE ]", self.browse_output_dir)
        browse_btn.pack(side="left")
        
        # Action buttons
        action_frame = tk.Frame(main_container, bg=HACKER_BG)
        action_frame.pack(fill="x", pady=(0, 15))
        
        self.download_btn = self.create_common_button(action_frame, "[ ⬇ DOWNLOAD ]", self.start_download, is_download=True)
        self.download_btn.pack(side="left", padx=(0, 10))
        
        self.play_btn = self.create_common_button(action_frame, "[ 📂 OPEN FOLDER ]", self.open_download_folder)
        self.play_btn.pack(side="left", padx=(0, 10))
        
        # Log section
        log_section = tk.Frame(main_container, bg=HACKER_BG)
        log_section.pack(fill="both", expand=True, pady=(0, 15))
        
        log_label = self.create_common_label(log_section, "[ 로그 ]")
        log_label.pack(anchor="w", pady=(0, 5))
        
        self.output_log = self.create_common_log_area(log_section)
        
        # Status and cancel button
        self.status_var = tk.StringVar(value="[ 상태: 대기중 ]")
        self.status_label, self.cancel_button = self.create_common_status_frame(
            main_container,
            self.status_var,
            self.cancel_download
        )
        
        # 개발자 정보
        dev_info_frame = tk.Frame(main_container, bg=HACKER_BG)
        dev_info_frame.pack(fill="x", pady=(0, 10))
        
        dev_info_label = tk.Label(
            dev_info_frame,
            text="이미지 다운로더(gallery-dl): @mikf | 영상 다운로더(yt-dlp): @yt-dlp | GUI 개발자: @noName_Come | 버전: V1.6",
            font=("Malgun Gothic", 10),
            bg=HACKER_BG,
            fg=HACKER_ACCENT
        )
        dev_info_label.pack(side="left", padx=10)
        
        # 첫 번째 URL 입력 필드 추가
        self.add_url_field()

    def init_ytdlp_ui(self):
        """yt-dlp 다운로더 탭 UI 초기화"""
        main_container = tk.Frame(self.ytdlp_frame, bg=HACKER_BG)
        main_container.pack(padx=20, pady=20, fill="both", expand=True)
        
        # Title
        title_frame = tk.Frame(main_container, bg=HACKER_BG)
        title_frame.pack(fill="x", pady=(0, 15))
        
        title_label = tk.Label(title_frame, text="[ 유튜브 다운로더 ]", font=("Malgun Gothic", 16, "bold"), bg=HACKER_BG, fg=HACKER_GREEN)
        title_label.pack(side="left")
        
        # YouTube options section
        youtube_section = tk.Frame(main_container, bg=HACKER_BG)
        youtube_section.pack(fill="x", pady=(0, 15))
        
        youtube_label = tk.Label(youtube_section, text="[ 옵션 선택 ]", font=("Malgun Gothic", 12, "bold"), bg=HACKER_BG, fg=HACKER_GREEN)
        youtube_label.pack(anchor="w", pady=(0, 5))
        
        self.youtube_frame = tk.Frame(youtube_section, bg=HACKER_BG)
        self.youtube_frame.pack(fill="x")
        
        resolution_label = tk.Label(self.youtube_frame, text="해상도:", font=("Malgun Gothic", 12), bg=HACKER_BG, fg=HACKER_GREEN)
        resolution_label.pack(side="left", padx=(0, 10))
        
        self.resolution_var = tk.StringVar(value="720")
        for res in ["720", "1080", "1440", "2160"]:
            btn = tk.Radiobutton(self.youtube_frame, text=f"[{res}]", variable=self.resolution_var, value=res, font=("Malgun Gothic", 12), bg=HACKER_BG, fg=HACKER_GREEN, selectcolor=HACKER_DARK, activebackground=HACKER_BG, activeforeground=HACKER_GREEN, cursor="hand2")
            btn.pack(side="left", padx=(0, 15))
        
        self.audio_only_var = tk.BooleanVar(value=False)
        self.audio_only_var.trace_add("write", self.toggle_resolution_buttons)  # MP3 선택 시 해상도 버튼 비활성화
        audio_cb = tk.Checkbutton(self.youtube_frame, text="[ MP3 ONLY ]", variable=self.audio_only_var, font=("Malgun Gothic", 12), bg=HACKER_BG, fg=HACKER_GREEN, selectcolor=HACKER_DARK, activebackground=HACKER_BG, activeforeground=HACKER_GREEN, cursor="hand2")
        audio_cb.pack(side="left")
        
        # URL input section with scrollable container
        url_section = tk.Frame(main_container, bg=HACKER_BG)
        url_section.pack(fill="x", pady=(0, 15))
        
        url_label = tk.Label(url_section, text="[ URL 입력 ]", font=("Malgun Gothic", 12, "bold"), bg=HACKER_BG, fg=HACKER_GREEN)
        url_label.pack(anchor="w", pady=(0, 5))
        
        # Create a frame to hold the canvas and scrollbar
        url_scroll_frame = tk.Frame(url_section, bg=HACKER_BG)
        url_scroll_frame.pack(fill="x", expand=True)
        url_scroll_frame.configure(height=80)  # 높이 설정
        url_scroll_frame.pack_propagate(False)  # 크기 고정
        
        # Create canvas and scrollbar
        self.yt_url_canvas = tk.Canvas(url_scroll_frame, bg=HACKER_BG, highlightthickness=0)
        yt_url_scrollbar = ttk.Scrollbar(url_scroll_frame, orient="vertical", command=self.yt_url_canvas.yview)
        
        # Create a frame inside canvas to hold URL entries
        self.yt_url_container = tk.Frame(self.yt_url_canvas, bg=HACKER_BG)
        self.yt_url_container.bind("<Configure>", lambda e: self.yt_url_canvas.configure(scrollregion=self.yt_url_canvas.bbox("all")))
        
        # Add the URL container frame to the canvas
        self.yt_url_canvas.create_window((0, 0), window=self.yt_url_container, anchor="nw", width=740)  # 고정된 너비 설정
        self.yt_url_canvas.configure(yscrollcommand=yt_url_scrollbar.set)
        
        # Pack canvas and scrollbar (유튜브 탭)
        self.yt_url_canvas.pack(side="left", fill="both", expand=True)
        # 스크롤바는 처음에 숨김
        self.yt_url_scrollbar = yt_url_scrollbar  # 나중에 참조하기 위해 저장
        
        # URL control buttons
        url_controls = tk.Frame(url_section, bg=HACKER_BG)
        url_controls.pack(fill="x", pady=(10, 0))
        
        self.add_yt_url_btn = tk.Button(url_controls, text="[ + ADD URL ]", font=("Malgun Gothic", 12, "bold"), bg=HACKER_ACCENT, fg=HACKER_BG, relief="flat", activebackground=HACKER_GREEN, activeforeground=HACKER_BG, command=self.add_yt_url_field, cursor="hand2", borderwidth=1, highlightthickness=1, highlightbackground=HACKER_BORDER, padx=15, pady=5)
        self.add_yt_url_btn.pack(side="left", padx=(0, 10))
        
        self.remove_yt_url_btn = tk.Button(url_controls, text="[ - REMOVE URL ]", font=("Malgun Gothic", 12, "bold"), bg=HACKER_ACCENT, fg=HACKER_BG, relief="flat", activebackground=HACKER_GREEN, activeforeground=HACKER_BG, command=self.remove_yt_url_field, cursor="hand2", borderwidth=1, highlightthickness=1, highlightbackground=HACKER_BORDER, padx=15, pady=5)
        self.remove_yt_url_btn.pack(side="left", padx=(0, 10))

        self.clear_yt_url_btn = tk.Button(url_controls, text="[ URL 초기화 ]", font=("Malgun Gothic", 12, "bold"), bg=HACKER_ACCENT, fg=HACKER_BG, relief="flat", activebackground=HACKER_GREEN, activeforeground=HACKER_BG, command=self.clear_all_yt_urls, cursor="hand2", borderwidth=1, highlightthickness=1, highlightbackground=HACKER_BORDER, padx=15, pady=5)
        self.clear_yt_url_btn.pack(side="left")
        
        # Output directory section (YouTube)
        output_section = tk.Frame(main_container, bg=HACKER_BG)
        output_section.pack(fill="x", pady=(0, 15))
        
        output_label = tk.Label(output_section, text="[ 저장위치 ]", font=("Malgun Gothic", 12, "bold"), bg=HACKER_BG, fg=HACKER_GREEN)
        output_label.pack(anchor="w", pady=(0, 5))
        
        output_frame = tk.Frame(output_section, bg=HACKER_BG)
        output_frame.pack(fill="x")
        
        self.yt_output_dir_var = tk.StringVar(value=self.stored_dir or os.getcwd())
        self.yt_output_entry = tk.Entry(output_frame, textvariable=self.yt_output_dir_var, width=50, font=("Malgun Gothic", 12), bg=HACKER_DARK, fg=HACKER_GREEN, insertbackground=HACKER_GREEN, relief="flat", highlightthickness=1, highlightbackground=HACKER_BORDER)
        self.yt_output_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        
        browse_btn = tk.Button(output_frame, text="[ BROWSE ]", font=("Malgun Gothic", 12, "bold"), bg=HACKER_ACCENT, fg=HACKER_BG, relief="flat", activebackground=HACKER_GREEN, activeforeground=HACKER_BG, command=lambda: self.browse_output_dir_yt(), cursor="hand2", borderwidth=1, highlightthickness=1, highlightbackground=HACKER_BORDER, padx=15, pady=5)
        browse_btn.pack(side="left")
        
        # Action buttons (YouTube)
        action_frame = tk.Frame(main_container, bg=HACKER_BG)
        action_frame.pack(fill="x", pady=(0, 15))
        
        self.yt_download_btn = tk.Button(action_frame, text="[ ⬇ DOWNLOAD ]", font=("Malgun Gothic", 12, "bold"), width=15, bg=DOWNLOAD_BTN_COLOR, fg=HACKER_BG, relief="flat", activebackground=DOWNLOAD_BTN_HOVER, activeforeground=HACKER_BG, command=self.start_yt_download, cursor="hand2", borderwidth=1, highlightthickness=1, highlightbackground=HACKER_BORDER, padx=15, pady=5)
        self.yt_download_btn.pack(side="left", padx=(0, 10))
        
        self.yt_play_btn = tk.Button(action_frame, text="[ 📂 OPEN FOLDER ]", font=("Malgun Gothic", 12, "bold"), bg=HACKER_ACCENT, fg=HACKER_BG, relief="flat", activebackground=HACKER_GREEN, activeforeground=HACKER_BG, command=self.open_download_folder_yt, cursor="hand2", borderwidth=1, highlightthickness=1, highlightbackground=HACKER_BORDER, padx=15, pady=5)
        self.yt_play_btn.pack(side="left", padx=(0, 10))
        
        # Log section (YouTube)
        log_section = tk.Frame(main_container, bg=HACKER_BG)
        log_section.pack(fill="both", expand=True, pady=(0, 15))
        
        log_label = tk.Label(log_section, text="[ 로그 ]", font=("Malgun Gothic", 12, "bold"), bg=HACKER_BG, fg=HACKER_GREEN)
        log_label.pack(anchor="w", pady=(0, 5))
        
        log_frame = tk.Frame(log_section, bg=HACKER_BG)
        log_frame.pack(fill="both", expand=True)
        
        self.yt_output_log = tk.Text(log_frame, width=90, height=10, font=("Consolas", 10), bg=HACKER_DARK, fg=HACKER_GREEN, insertbackground=HACKER_GREEN, relief="flat", wrap="word", highlightthickness=1, highlightbackground=HACKER_BORDER)
        scrollbar = ttk.Scrollbar(log_frame, orient="vertical", command=self.yt_output_log.yview, style="Custom.Vertical.TScrollbar")
        
        self.yt_output_log.configure(yscrollcommand=scrollbar.set)
        self.yt_output_log.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Status and cancel button (YouTube)
        status_frame = tk.Frame(main_container, bg=HACKER_BG)
        status_frame.pack(fill="x", pady=(20, 10))
        
        separator = ttk.Separator(main_container, orient='horizontal')
        separator.pack(fill='x', pady=(0, 10))
        
        self.yt_status_var = tk.StringVar(value="[ 상태: 대기중 ]")
        self.yt_status_label = tk.Label(status_frame, textvariable=self.yt_status_var, anchor='w', font=("Malgun Gothic", 12), bg=HACKER_BG, fg=HACKER_GREEN)
        self.yt_status_label.pack(side="left", fill='x', expand=True)
        
        self.yt_cancel_button = tk.Button(status_frame, text="[ ⛔ CANCEL ]", font=("Malgun Gothic", 12), bg=HACKER_DARK, fg=HACKER_RED, relief="flat", activebackground=HACKER_RED, activeforeground=HACKER_BG, command=self.cancel_yt_download, state=tk.DISABLED, cursor="hand2", borderwidth=1, highlightthickness=1, highlightbackground=HACKER_BORDER)
        self.yt_cancel_button.pack(side="right", padx=10)

        # 개발자 정보 프레임
        dev_info_frame = tk.Frame(main_container, bg=HACKER_BG)
        dev_info_frame.pack(fill="x", pady=(0, 10))
        
        dev_info_label = tk.Label(dev_info_frame, text="이미지 다운로더(gallery-dl): @mikf | 영상 다운로더(yt-dlp): @yt-dlp | GUI 개발자: @noName_Come | 버전: V1.6", font=("Malgun Gothic", 10), bg=HACKER_BG, fg=HACKER_ACCENT)
        dev_info_label.pack(side="left", padx=10)
        
        # 첫 번째 URL 입력 필드 추가
        self.add_yt_url_field()

    def toggle_resolution_buttons(self, *args):
        """MP3 선택 시 해상도 버튼 비활성화/활성화"""
        state = tk.DISABLED if self.audio_only_var.get() else tk.NORMAL
        for child in self.youtube_frame.winfo_children():
            if isinstance(child, tk.Radiobutton):
                child.config(state=state)

    def add_url_field(self):
        row_frame = tk.Frame(self.url_container, bg=HACKER_BG)
        row_frame.pack(fill="x", pady=(0, 2))

        entry_style = {
            "font": ("Malgun Gothic", 12),
            "bg": HACKER_DARK,
            "fg": HACKER_GREEN,
            "insertbackground": HACKER_GREEN,
            "highlightbackground": HACKER_DARK,
            "highlightcolor": HACKER_GREEN,
            "highlightthickness": 1,
            "insertwidth": 2,
            "relief": "flat",
            "width": 100
        }

        url_entry = tk.Entry(row_frame, **entry_style)
        url_entry.insert(0, "URL을 입력하세요")
        url_entry.pack(side="top", fill="x", padx=2, ipady=5)
        url_entry.bind("<FocusIn>", lambda e: self.clear_placeholder(url_entry, "URL을 입력하세요"))
        url_entry.bind("<FocusOut>", lambda e: self.restore_placeholder(url_entry, "URL을 입력하세요"))

        filename_entry = tk.Entry(row_frame, **entry_style)
        filename_entry.insert(0, "파일이름 입력 (선택)")
        filename_entry.pack(side="top", fill="x", padx=2, pady=(2, 0), ipady=5)
        filename_entry.bind("<FocusIn>", lambda e: self.clear_placeholder(filename_entry, "파일이름 입력 (선택)"))
        filename_entry.bind("<FocusOut>", lambda e: self.restore_placeholder(filename_entry, "파일이름 입력 (선택)"))

        self.url_sets.append((url_entry, filename_entry, row_frame))
        
        # URL 세트가 3개 이하일 때는 프레임 높이 조절
        url_scroll_frame = self.url_canvas.master
        scrollbar = [child for child in url_scroll_frame.winfo_children() if isinstance(child, ttk.Scrollbar)][0]
        
        if len(self.url_sets) <= 3:
            new_height = 80 * len(self.url_sets)  # 각 URL 세트당 80px
            url_scroll_frame.configure(height=new_height)
            scrollbar.pack_forget()  # 스크롤바 숨기기
        else:
            scrollbar.pack(side="right", fill="y")  # 스크롤바 표시
        
        # Canvas 크기 업데이트
        self.url_container.update_idletasks()
        self.url_canvas.configure(scrollregion=self.url_canvas.bbox("all"))

        # 마우스 스크롤 바인딩 추가
        self.url_canvas.bind_all("<MouseWheel>", self._on_mousewheel)

    def _on_mousewheel(self, event):
        """마우스 스크롤 이벤트 처리"""
        self.url_canvas.yview_scroll(int(-1*(event.delta/120)), "units")

    def remove_url_field(self):
        if len(self.url_sets) > 1:
            _, _, row_frame = self.url_sets.pop()
            row_frame.destroy()

            # URL 세트가 3개 이하일 때 프레임 높이 조절
            url_scroll_frame = self.url_canvas.master
            scrollbar = [child for child in url_scroll_frame.winfo_children() if isinstance(child, ttk.Scrollbar)][0]
            
            if len(self.url_sets) <= 3:
                new_height = 80 * len(self.url_sets)  # 각 URL 세트당 80px
                url_scroll_frame.configure(height=new_height)
                scrollbar.pack_forget()  # 스크롤바 숨기기
            else:
                scrollbar.pack(side="right", fill="y")  # 스크롤바 표시

            # Canvas 크기 업데이트
            self.url_container.update_idletasks()
            self.url_canvas.configure(scrollregion=self.url_canvas.bbox("all"))

    def open_download_folder(self):
        if hasattr(self, 'last_community_path') and self.last_community_path:
            folder_path = self.last_community_path
        else:
            folder_path = self.output_dir_var.get().strip()

        if os.path.exists(folder_path):
            try:
                os.startfile(folder_path)
            except Exception as e:
                messagebox.showerror("오류", f"폴더 열기 실패:\n{e}")
        else:
            messagebox.showwarning("경고", "지정한 폴더가 존재하지 않습니다.")

    def download_thread(self, url, output_dir):
        # 로그 출력 함수 정의
        def log(msg):
            self.log_area.insert(tk.END, msg + "\n")
            self.log_area.see(tk.END)

        # 취소 확인 함수 정의
        def cancel():
            return self._cancel_requested

        # 다운로드 실행
        result = ytdlp_smart_download(
            url, output_dir, filename=None,
            log_func=self.thread_safe_log,
            resolution=self.resolution_var.get(),
            audio_only=self.audio_only_var.get(),
            cancel_check_func=cancel
        )

        # 다운로드 결과 처리
        if isinstance(result, str):
            self.last_community_path = result

        self.status_var.set("[ 상태: 완료 ]" if result else "[ 상태: 실패 ]")
        self.download_button.config(state="normal")
        self.cancel_button.config(state="disabled")

    def thread_safe_log(self, msg):
        # 스레드 안전한 로그 출력
        self.root.after(0, lambda: self._append_log(msg))

    def _append_log(self, msg):
        # 로그 메시지 추가
        self.output_log.config(state=tk.NORMAL)
        self.output_log.insert(tk.END, msg + '\n')
        self.output_log.see(tk.END)
        self.output_log.config(state=tk.DISABLED)

    def clear_placeholder(self, entry, placeholder):
        if entry.get() == placeholder:
            entry.delete(0, tk.END)

    def restore_placeholder(self, entry, placeholder):
        if not entry.get():
            entry.insert(0, placeholder)

    def download_multiple(self, url_info_list, output_dir):
        failed_urls = []
        total_urls = len(url_info_list)

        try:
            for idx, (url, filename) in enumerate(url_info_list, start=1):
                self.status_var.set(f"[ 상태: 다운로드 중 ({idx}/{total_urls}) ]")
                
                # 히토미 URL 체크
                if url.startswith("https://hitomi.la/"):
                    self.log(f"⚠ 히토미 URL이 감지되었습니다: {url}")
                    self.log("→ 히토미 다운로더 탭으로 이동하여 다운로드해주세요.")
                    failed_urls.append(url)
                    continue
                
                # YouTube URL 체크
                if is_youtube(url):
                    self.log(f"⚠ YouTube URL이 감지되었습니다: {url}")
                    self.log("→ yt-dlp 다운로더 탭으로 이동하여 다운로드해주세요.")
                    failed_urls.append(url)
                    continue
                
                # gallery-dl 다운로드 시도
                selected_exts = [ext for ext, var in self.filter_vars.items() if var.get()]
                # 선택된 확장자가 없으면 모든 확장자 허용
                if not selected_exts:
                    self.log("ℹ 선택된 확장자가 없어 모든 파일을 다운로드합니다.")
                
                success = gallery_download(
                    url=url,
                    output_dir=output_dir,
                    filename=filename,
                    selected_exts=selected_exts if selected_exts else None,  # 선택된 확장자가 없으면 None 전달
                    log_func=self.log,
                    status_func=self.status_var.set,
                    cancel_check_func=lambda: self._cancel_requested,
                    proc_register=self.processes.append
                )

                if not success:
                    self.log(f"❌ 실패: {url}")
                    failed_urls.append(url)
                else:
                    self.log(f"✅ 완료: {url}")

            if failed_urls:
                self.log("🚫 다음 URL에서 실패했습니다:")
                for f in failed_urls:
                    self.log(f"    - {f}")
                self.status_var.set("[ 상태: 일부 실패 ]")
            else:
                self.status_var.set("[ 상태: 완료 ]")
                self.log("✅ 모든 다운로드가 완료되었습니다!")
        finally:
            self.enable_ui()

    def start_download(self):
        self.resolution_warning_shown = False
        self._cancel_requested = False

        url_info = []

        for i, (url_entry, file_entry, _) in enumerate(self.url_sets, start=1):
            url = url_entry.get().strip()
            filename = file_entry.get().strip()

            if re.match(r'^https?://', url):
                if filename == "파일이름 입력 (선택)" or not filename:
                    filename = None
                url_info.append((url, filename))

        if not url_info:
            try:
                clip = self.root.clipboard_get()
                if re.match(r'^https?://', clip.strip()):
                    url_info.append((clip.strip(), None))
                else:
                    raise ValueError
            except:
                messagebox.showerror("오류", "URL을 입력하거나 클립보드에 유효한 링크가 있어야 합니다.")
                return

        output_dir = self.output_dir_var.get().strip()
        self.store_output_dir(output_dir)
        self.disable_ui()
        self.status_var.set("[ 상태: 다운로드 중 ]")
        self.log("다운로드를 시작합니다...")

        threading.Thread(target=self.download_multiple, args=(url_info, output_dir)).start()

    def cancel_download(self):
        self._cancel_requested = True
        self.status_var.set("[ 상태: 취소 중 ]")
        self.log("⛔ 취소 요청됨 → 모든 다운로드를 중지합니다...")

        for proc in self.processes:
            try:
                if os.name == "nt":
                    self.log(f"⚠ FORCE TERMINATION ATTEMPT (PID: {proc.pid})")
                    kill_proc_tree(proc.pid)  # ✅ 여기 핵심!
                else:
                    proc.terminate()
            except Exception as e:
                self.log(f"⚠️ PROCESS TERMINATION FAILED: {e}")

        self.processes.clear()
        self.enable_ui()

    def disable_ui(self):
        self.download_btn.config(state=tk.DISABLED)
        self.cancel_button.config(state=tk.NORMAL)

    def enable_ui(self):
        self.download_btn.config(state=tk.NORMAL)
        self.cancel_button.config(state=tk.DISABLED)

    def log(self, message):
        self.output_log.config(state=tk.NORMAL)
        self.output_log.insert(tk.END, message + "\n")
        self.output_log.see(tk.END)
        self.output_log.config(state=tk.DISABLED)

    def store_output_dir(self, path):
        try:
            with open(CONFIG_STORE, 'w', encoding='utf-8') as f:
                json.dump({"last_output_dir": path}, f, indent=4)
        except:
            pass

    def load_stored_output_dir(self):
        if os.path.exists(CONFIG_STORE):
            try:
                with open(CONFIG_STORE, 'r', encoding='utf-8') as f:
                    return json.load(f).get("last_output_dir")
            except:
                return None

    def browse_output_dir(self):
        dir = filedialog.askdirectory(initialdir=self.output_dir_var.get())
        if dir:
            self.output_dir_var.set(dir)
            self.store_output_dir(dir)

    def open_or_create_config(self):
            config_path = os.path.join(os.environ.get("USERPROFILE", ""), "gallery-dl", "config.json")
            config_dir = os.path.dirname(config_path)
            os.makedirs(config_dir, exist_ok=True)
            if not os.path.exists(config_path):
                with open(config_path, "w", encoding="utf-8") as f:
                    json.dump({}, f, indent=4)
            try:
                os.startfile(config_path)
            except Exception as e:
                messagebox.showerror("오류", f"config.json 열기 실패:\n{e}")

    def smart_download(self, url, output_dir, num, filename):
        try:
            if is_youtube(url):
                self.log("⚠ 유튜브 URL은 yt-dlp 다운로더 탭에서 다운로드해주세요.")
                self.log("→ yt-dlp 다운로더 탭으로 이동 후 다운로드를 진행해주세요.")
                return False
            else:
                selected_exts = [ext for ext, var in self.filter_vars.items() if var.get()]
                return gallery_download(
                    url=url,
                    output_dir=output_dir,
                    filename=filename,
                    selected_exts=selected_exts,
                    log_func=self.log,
                    status_func=self.status_var.set,
                    cancel_check_func=lambda: self._cancel_requested,
                    proc_register=self.processes.append
                )
        except Exception as e:
            self.log(f"❌ 다운로드 중 오류 발생: {str(e)}")
            return False

    def open_new_window(self):
        """새 창 열기"""
        # 새 창 생성을 위한 Toplevel 대신 새로운 프로세스 시작
        if sys.platform == "win32":
            subprocess.Popen([sys.executable, sys.argv[0]], creationflags=subprocess.CREATE_NEW_CONSOLE)
        else:
            subprocess.Popen([sys.executable, sys.argv[0]])

    def clear_all_urls(self):
        # 모든 URL 입력 필드 초기화
        for url_entry, filename_entry, _ in self.url_sets:
            url_entry.delete(0, tk.END)
            url_entry.insert(0, "URL을 입력하세요")
            filename_entry.delete(0, tk.END)
            filename_entry.insert(0, "파일이름 입력 (선택)")

        # 첫 번째 URL 세트만 남기고 나머지 제거
        while len(self.url_sets) > 1:
            _, _, row_frame = self.url_sets.pop()
            row_frame.destroy()

        # 프레임 크기를 초기 크기로 복원
        url_scroll_frame = self.url_canvas.master
        scrollbar = [child for child in url_scroll_frame.winfo_children() if isinstance(child, ttk.Scrollbar)][0]
        url_scroll_frame.configure(height=80)
        scrollbar.pack_forget()  # 스크롤바 숨기기
        
        # Canvas 크기 업데이트
        self.url_container.update_idletasks()
        self.url_canvas.configure(scrollregion=self.url_canvas.bbox("all"))

    def init_help_tab(self):
        """도움말 탭 초기화"""
        help_frame = tk.Frame(self.help_frame, bg=HACKER_BG)
        help_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # 도움말 내용을 위한 Text 위젯과 스크롤바를 포함할 프레임
        text_frame = tk.Frame(help_frame, bg=HACKER_BG)
        text_frame.pack(fill="both", expand=True)
        
        # 도움말 내용을 표시할 Text 위젯
        help_text_widget = tk.Text(text_frame, 
                                 font=("Malgun Gothic", 11),
                                 bg=HACKER_DARK,
                                 fg=HACKER_ACCENT,
                                 relief="flat",
                                 wrap="word",
                                 highlightthickness=1,
                                 highlightbackground=HACKER_BORDER,
                                 padx=10,
                                 pady=10)
        
        # 스크롤바 추가
        help_scrollbar = ttk.Scrollbar(text_frame, orient="vertical", command=help_text_widget.yview)
        help_text_widget.configure(yscrollcommand=help_scrollbar.set)
        
        # 스크롤바와 Text 위젯 배치
        help_text_widget.pack(side="left", fill="both", expand=True)
        help_scrollbar.pack(side="right", fill="y")
        
        # 도움말 내용
        help_content = """
================================================================
🚀 프로그램 소개 🚀
================================================================
이 프로그램으로 다음 사이트에서 콘텐츠를 쉽게 다운로드할 수 있습니다:

1. 케모노파티 (Kemono.su)
   - 좋아하는 크리에이터의 게시물 한 번에 다운로드
   - 이미지, 동영상 등 모든 첨부파일 자동 저장

2. 유튜브 (YouTube)
   - 고화질 영상 다운로드 (720p부터 4K까지)
   - 음악만 필요하 다면 MP3로 추출 가능
   - 채널별로 깔끔하게 정리되어 저장

3. 히토미 (Hitomi.la)
   - 이미지 갤러리 빠르게 다운로드
   - 작품 정보도 함께 저장

================================================================
💡 간단 사용법 💡
================================================================

1. URL 붙여넣기
   - 원하는 콘텐츠의 주소를 복사해서 입력창에 붙여넣으세요
   - 여러 개의 URL을 한 번에 처리할 수 있어요

2. 저장 위치 설정
   - '저장 위치' 버튼으로 파일이 저장될 폴더를 선택하세요
   - 선택하지 않아도 기본 폴더에 저장됩니다

3. 다운로드 클릭
   - '다운로드 시작' 버튼을 누르면 자동으로 진행됩니다
   - 아래 로그창에서 진행 상황을 확인할 수 있어요

4. 다운로드 팁
   - 백신 프로그램이 다운로드를 방해할 수 있으니 잠시 꺼두세요
   - 안정적인 인터넷 연결이 필요합니다
   - 큰 파일은 다운로드에 시간이 걸릴 수 있어요

================================================================
⚙️ config.json 설정하기 ⚙️
================================================================

설정 파일 적용 방법:
1. 아래 링크에서 config.json 파일 다운로드
   👉 https://github.com/noNameCome/gallery-dl-yt-dlp-downloader-V1.5/blob/main/config.json

2. 내용 전체 복사 후 다음 경로에 붙여넣기:
   `C:\\Users\\[사용자이름]\\gallery-dl\\config.json`
   (프로그램의 'config 열기' 버튼을 누르면 바로 이동할 수 있어요)

고급 설정이 필요하다면:
- CMD 창 명령어 `gallery-dl --list-keywords (url)`로 사용 가능한 옵션 확인

================================================================
👨‍💻 개발 정보 👨‍💻
================================================================
• gallery-dl (이미지 다운로더): @mikf https://github.com/mikf/gallery-dl
• yt-dlp (영상 다운로더): @yt-dlp https://github.com/yt-dlp/yt-dlp
• GUI 개발: @noName_Come https://github.com/noNameCome/kemyouhit-downloader-V1.6

"""
        
        # Text 위젯에 내용 추가
        help_text_widget.insert("1.0", help_content)
        
        # Text 위젯을 읽기 전용으로 설정
        help_text_widget.configure(state="disabled")

    def browse_output_dir_yt(self):
        """YouTube 탭용 출력 디렉토리 선택"""
        dir = filedialog.askdirectory(initialdir=self.yt_output_dir_var.get())
        if dir:
            self.yt_output_dir_var.set(dir)
            self.store_output_dir(dir)

    def open_download_folder_yt(self):
        """YouTube 탭용 다운로드 폴더 열기"""
        folder_path = os.path.join(self.yt_output_dir_var.get().strip(), "YouTube")
        if os.path.exists(folder_path):
            try:
                os.startfile(folder_path)
            except Exception as e:
                messagebox.showerror("오류", f"폴더 열기 실패:\n{e}")
        else:
            messagebox.showwarning("경고", "YouTube 폴더가 존재하지 않습니다.")

    def add_yt_url_field(self):
        row_frame = tk.Frame(self.yt_url_container, bg=HACKER_BG)
        row_frame.pack(fill="x", pady=(0, 2))

        entry_style = {
            "font": ("Malgun Gothic", 12),
            "bg": HACKER_DARK,
            "fg": HACKER_GREEN,
            "insertbackground": HACKER_GREEN,
            "highlightbackground": HACKER_DARK,
            "highlightcolor": HACKER_GREEN,
            "highlightthickness": 1,
            "insertwidth": 2,
            "relief": "flat",
            "width": 100
        }

        url_entry = tk.Entry(row_frame, **entry_style)
        url_entry.insert(0, "URL을 입력하세요")
        url_entry.pack(side="top", fill="x", padx=2, ipady=5)
        url_entry.bind("<FocusIn>", lambda e: self.clear_placeholder(url_entry, "URL을 입력하세요"))
        url_entry.bind("<FocusOut>", lambda e: self.restore_placeholder(url_entry, "URL을 입력하세요"))

        filename_entry = tk.Entry(row_frame, **entry_style)
        filename_entry.insert(0, "파일이름 입력 (선택)")
        filename_entry.pack(side="top", fill="x", padx=2, pady=(2, 0), ipady=5)
        filename_entry.bind("<FocusIn>", lambda e: self.clear_placeholder(filename_entry, "파일이름 입력 (선택)"))
        filename_entry.bind("<FocusOut>", lambda e: self.restore_placeholder(filename_entry, "파일이름 입력 (선택)"))

        self.yt_url_sets.append((url_entry, filename_entry, row_frame))
        
        # URL 세트가 3개 이하일 때는 프레임 높이 조절
        yt_url_scroll_frame = self.yt_url_canvas.master
        
        if len(self.yt_url_sets) <= 3:
            new_height = 80 * len(self.yt_url_sets)  # 각 URL 세트당 80px
            yt_url_scroll_frame.configure(height=new_height)
            self.yt_url_scrollbar.pack_forget()  # 스크롤바 숨기기
        else:
            self.yt_url_scrollbar.pack(side="right", fill="y")  # 스크롤바 표시
        
        # Canvas 크기 업데이트
        self.yt_url_container.update_idletasks()
        self.yt_url_canvas.configure(scrollregion=self.yt_url_canvas.bbox("all"))

        # 마우스 스크롤 바인딩 추가
        self.yt_url_canvas.bind_all("<MouseWheel>", self._on_yt_mousewheel)

    def _on_yt_mousewheel(self, event):
        """유튜브 탭 마우스 스크롤 이벤트 처리"""
        self.yt_url_canvas.yview_scroll(int(-1*(event.delta/120)), "units")

    def remove_yt_url_field(self):
        """YouTube 탭에서 URL 입력 필드 제거"""
        if len(self.yt_url_sets) > 1:
            _, _, row_frame = self.yt_url_sets.pop()
            row_frame.destroy()

            # URL 세트가 3개 이하일 때 프레임 높이 조절
            yt_url_scroll_frame = self.yt_url_canvas.master
            scrollbar = [child for child in yt_url_scroll_frame.winfo_children() if isinstance(child, ttk.Scrollbar)][0]
            
            if len(self.yt_url_sets) <= 3:
                new_height = 80 * len(self.yt_url_sets)  # 각 URL 세트당 80px
                yt_url_scroll_frame.configure(height=new_height)
                scrollbar.pack_forget()  # 스크롤바 숨기기
            else:
                scrollbar.pack(side="right", fill="y")  # 스크롤바 표시

            # Canvas 크기 업데이트
            self.yt_url_container.update_idletasks()
            self.yt_url_canvas.configure(scrollregion=self.yt_url_canvas.bbox("all"))

    def clear_all_yt_urls(self):
        """YouTube 탭의 모든 URL 입력 필드 초기화"""
        for url_entry, filename_entry, _ in self.yt_url_sets:
            url_entry.delete(0, tk.END)
            url_entry.insert(0, "URL을 입력하세요")
            filename_entry.delete(0, tk.END)
            filename_entry.insert(0, "파일이름 입력 (선택)")

        while len(self.yt_url_sets) > 1:
            _, _, row_frame = self.yt_url_sets.pop()
            row_frame.destroy()

        # 프레임 크기를 초기 크기로 복원
        yt_url_scroll_frame = self.yt_url_canvas.master
        yt_url_scroll_frame.configure(height=80)
        self.yt_url_scrollbar.pack_forget()  # 스크롤바 숨기기
        
        # Canvas 크기 업데이트
        self.yt_url_container.update_idletasks()
        self.yt_url_canvas.configure(scrollregion=self.yt_url_canvas.bbox("all"))

    def start_yt_download(self):
        """YouTube 다운로드 시작"""
        url_info = []
        self._cancel_requested = False  # 다운로드 시작 시 취소 플래그 초기화

        for url_entry, filename_entry, _ in self.yt_url_sets:
            url = url_entry.get().strip()
            filename = filename_entry.get().strip()

            if re.match(r'^https?://', url):
                if filename == "파일이름 입력 (선택)" or not filename:
                    filename = None
                url_info.append((url, filename))

        if not url_info:
            try:
                clip = self.root.clipboard_get()
                if re.match(r'^https?://', clip.strip()):
                    url_info.append((clip.strip(), None))
                else:
                    raise ValueError
            except:
                messagebox.showerror("오류", "URL을 입력하거나 클립보드에 유효한 링크가 있어야 합니다.")
                return
            
        output_dir = self.yt_output_dir_var.get().strip()
        self.store_output_dir(output_dir)
        
        self.disable_yt_ui()
        self.yt_status_var.set("[ 상태: 다운로드 중 ]")
        self.log_yt("다운로드를 시작합니다...")
        
        threading.Thread(target=self.download_multiple_yt, args=(url_info, output_dir)).start()

    def download_multiple_yt(self, url_info_list, output_dir):
        """여러 YouTube URL 다운로드"""
        failed_urls = []
        total_urls = len(url_info_list)

        try:
            # ffmpeg 경로 설정
            ffmpeg_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "ffmpeg")
            if not os.path.exists(ffmpeg_path):
                self.log_yt("⚠ ffmpeg 폴더를 찾을 수 없습니다.")
                return

            for idx, (url, filename) in enumerate(url_info_list, start=1):
                if self._cancel_requested:
                    self.log_yt("⛔ 다운로드가 취소되었습니다.")
                    break

                self.yt_status_var.set(f"[ 상태: 다운로드 중 ({idx}/{total_urls}) ]")
                self.log_yt(f"🔄 다운로드 시작: {url}")
                
                # YouTube URL 체크
                if not is_youtube(url):
                    self.log_yt(f"⚠ YouTube URL이 아닙니다: {url}")
                    self.log_yt("→ gallery-dl 다운로더 탭으로 이동하여 다운로드해주세요.")
                    failed_urls.append(url)
                    continue
                
                # MP3가 아닐 때만 해상도 체크
                if not self.audio_only_var.get():
                    resolution = self.resolution_var.get()
                    if resolution not in ["720", "1080", "1440", "2160"]:
                        if not self.resolution_warning_shown:
                            messagebox.showwarning("해상도 선택 필요", "⚠ 해상도를 선택해주세요!\n\n유튜브 영상 다운로드를 위해 해상도를 지정해야 합니다.")
                            self.resolution_warning_shown = True
                        self.log_yt("⚠ 다운로드 취소: 해상도가 선택되지 않았습니다.")
                        failed_urls.append(url)
                        continue
                
                try:
                    # YouTube 디렉토리 생성
                    youtube_dir = os.path.join(output_dir, "YouTube")
                    os.makedirs(youtube_dir, exist_ok=True)
                    
                    # 출력 템플릿 설정
                    if filename:
                        output_template = os.path.join(youtube_dir, "%(uploader)s", f"{filename}.%(ext)s")
                    else:
                        output_template = os.path.join(youtube_dir, "%(uploader)s", "%(title)s.%(ext)s")

                    command = [
                        "yt-dlp",
                        "--no-warnings",
                        "--no-playlist",  # 플레이리스트 다운로드 방지
                        "--ffmpeg-location", ffmpeg_path,  # ffmpeg 경로 지정
                    ]

                    if self.audio_only_var.get():
                        command.extend([
                            "-x",  # 오디오 추출
                            "--audio-format", "mp3",  # MP3 형식으로 변환
                            "--audio-quality", "0",  # 최고 품질
                            "-f", "bestaudio/best",  # 최고 품질 오디오 선택
                            "--postprocessor-args", "-ar 44100",  # 샘플레이트 설정
                            "--embed-thumbnail",  # 썸네일 삽입
                            "--embed-metadata",  # 메타데이터 삽입
                        ])
                    else:
                        command.extend([
                            "-f", f"bestvideo[height<={resolution}]+bestaudio/best[height<={resolution}]",
                            "--merge-output-format", "mp4"  # MP4로 병합
                        ])

                    command.extend(["-o", output_template, url])
                    
                    self.log_yt("⬇️ 다운로드 시작...")
                    process = subprocess.Popen(
                        command,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True,
                        creationflags=subprocess.CREATE_NO_WINDOW
                    )
                    
                    while True:
                        if self._cancel_requested:
                            process.terminate()
                            break
                            
                        output = process.stdout.readline()
                        if output == '' and process.poll() is not None:
                            break
                        if output:
                            self.log_yt(output.strip())
                    
                    if process.returncode == 0:
                        self.log_yt(f"✅ 다운로드 완료: {url}")
                    else:
                        error = process.stderr.read()
                        self.log_yt(f"❌ 다운로드 실패: {error}")
                        failed_urls.append(url)
                        
                except Exception as e:
                    self.log_yt(f"❌ 오류 발생: {str(e)}")
                    failed_urls.append(url)

            if not self._cancel_requested:
                if failed_urls:
                    self.log_yt("🚫 다음 URL에서 실패했습니다:")
                    for f in failed_urls:
                        self.log_yt(f"    - {f}")
                    self.yt_status_var.set("[ 상태: 일부 실패 ]")
                else:
                    self.yt_status_var.set("[ 상태: 완료 ]")
                    self.log_yt("✅ 모든 다운로드가 완료되었습니다!")
        finally:
            self.enable_yt_ui()

    def cancel_yt_download(self):
        """YouTube 다운로드 취소"""
        self._cancel_requested = True  # 취소 플래그 설정
        self.yt_cancel_button.config(state="disabled")
        self.yt_status_var.set("[ 상태: 취소 중 ]")
        self.log_yt("⛔ 취소 요청됨 → 다운로드를 중지합니다...")
        
        for proc in self.processes:
            try:
                if os.name == "nt":
                    kill_proc_tree(proc.pid)
                else:
                    proc.terminate()
            except:
                pass
                
        self.processes.clear()
        self.enable_yt_ui()

    def disable_yt_ui(self):
        """YouTube 탭 UI 비활성화"""
        self.yt_download_btn.config(state="disabled")
        self.yt_cancel_button.config(state="normal")

    def enable_yt_ui(self):
        """YouTube 탭 UI 활성화"""
        self.yt_download_btn.config(state="normal")
        self.yt_cancel_button.config(state="disabled")

    def log_yt(self, message):
        """YouTube 탭 로그 출력"""
        self.yt_output_log.config(state=tk.NORMAL)
        self.yt_output_log.insert(tk.END, message + "\n")
        self.yt_output_log.see(tk.END)
        self.yt_output_log.config(state=tk.DISABLED)

    def init_hitomi_ui(self):
        """히토미 다운로더 탭 UI 초기화"""
        main_container = tk.Frame(self.hitomi_frame, bg=HACKER_BG)
        main_container.pack(padx=20, pady=20, fill="both", expand=True)
        
        # Title with ASCII art style
        title_frame = tk.Frame(main_container, bg=HACKER_BG)
        title_frame.pack(fill="x", pady=(0, 15))
        
        title_label = tk.Label(title_frame, text="[ 히토미 다운로더 ]", font=("Malgun Gothic", 16, "bold"), bg=HACKER_BG, fg=HACKER_GREEN)
        title_label.pack(side="left")
        
        # URL input section with scrollable container
        url_section = tk.Frame(main_container, bg=HACKER_BG)
        url_section.pack(fill="x", pady=(0, 15))
        
        url_label = tk.Label(url_section, text="[ URL 입력 ]", font=("Malgun Gothic", 12, "bold"), bg=HACKER_BG, fg=HACKER_GREEN)
        url_label.pack(anchor="w", pady=(0, 5))
        
        # Create a frame to hold the canvas and scrollbar
        url_scroll_frame = tk.Frame(url_section, bg=HACKER_BG)
        url_scroll_frame.pack(fill="x", expand=True)
        url_scroll_frame.configure(height=80)  # 높이 설정
        url_scroll_frame.pack_propagate(False)  # 크기 고정
        
        # Create canvas and scrollbar
        self.hitomi_url_canvas = tk.Canvas(url_scroll_frame, bg=HACKER_BG, highlightthickness=0)
        hitomi_url_scrollbar = ttk.Scrollbar(url_scroll_frame, orient="vertical", command=self.hitomi_url_canvas.yview)
        
        # Create a frame inside canvas to hold URL entries
        self.hitomi_url_container = tk.Frame(self.hitomi_url_canvas, bg=HACKER_BG)
        self.hitomi_url_container.bind("<Configure>", lambda e: self.hitomi_url_canvas.configure(scrollregion=self.hitomi_url_canvas.bbox("all")))
        
        # Add the URL container frame to the canvas
        self.hitomi_url_canvas.create_window((0, 0), window=self.hitomi_url_container, anchor="nw", width=740)  # 고정된 너비 설정
        self.hitomi_url_canvas.configure(yscrollcommand=hitomi_url_scrollbar.set)
        
        # Pack canvas and scrollbar (히토미 탭)
        self.hitomi_url_canvas.pack(side="left", fill="both", expand=True)
        # 스크롤바는 처음에 숨김
        self.hitomi_url_scrollbar = hitomi_url_scrollbar  # 나중에 참조하기 위해 저장
        
        # URL control buttons
        url_controls = tk.Frame(url_section, bg=HACKER_BG)
        url_controls.pack(fill="x", pady=(10, 0))
        
        self.add_hitomi_url_btn = tk.Button(url_controls, text="[ + ADD URL ]", font=("Malgun Gothic", 12, "bold"), 
                                          bg=HACKER_ACCENT, fg=HACKER_BG, relief="flat", 
                                          activebackground=HACKER_GREEN, activeforeground=HACKER_BG, 
                                          command=self.add_hitomi_url_field, cursor="hand2", 
                                          borderwidth=1, highlightthickness=1, highlightbackground=HACKER_BORDER, 
                                          padx=15, pady=5)
        self.add_hitomi_url_btn.pack(side="left", padx=(0, 10))
        
        self.remove_hitomi_url_btn = tk.Button(url_controls, text="[ - REMOVE URL ]", font=("Malgun Gothic", 12, "bold"), 
                                             bg=HACKER_ACCENT, fg=HACKER_BG, relief="flat", 
                                             activebackground=HACKER_GREEN, activeforeground=HACKER_BG, 
                                             command=self.remove_hitomi_url_field, cursor="hand2", 
                                             borderwidth=1, highlightthickness=1, highlightbackground=HACKER_BORDER, 
                                             padx=15, pady=5)
        self.remove_hitomi_url_btn.pack(side="left", padx=(0, 10))

        self.clear_hitomi_url_btn = tk.Button(url_controls, text="[ URL 초기화 ]", font=("Malgun Gothic", 12, "bold"), 
                                            bg=HACKER_ACCENT, fg=HACKER_BG, relief="flat", 
                                            activebackground=HACKER_GREEN, activeforeground=HACKER_BG, 
                                            command=self.clear_all_hitomi_urls, cursor="hand2", 
                                            borderwidth=1, highlightthickness=1, highlightbackground=HACKER_BORDER, 
                                            padx=15, pady=5)
        self.clear_hitomi_url_btn.pack(side="left")
        
        # Output directory section
        output_section = tk.Frame(main_container, bg=HACKER_BG)
        output_section.pack(fill="x", pady=(0, 15))
        
        output_label = tk.Label(output_section, text="[ 저장위치 ]", font=("Malgun Gothic", 12, "bold"), bg=HACKER_BG, fg=HACKER_GREEN)
        output_label.pack(anchor="w", pady=(0, 5))
        
        output_frame = tk.Frame(output_section, bg=HACKER_BG)
        output_frame.pack(fill="x")
        
        self.hitomi_output_dir_var = tk.StringVar(value=self.stored_dir or os.getcwd())
        self.hitomi_output_entry = tk.Entry(output_frame, textvariable=self.hitomi_output_dir_var, 
                                          width=50, font=("Malgun Gothic", 12), bg=HACKER_DARK, 
                                          fg=HACKER_GREEN, insertbackground=HACKER_GREEN, 
                                          relief="flat", highlightthickness=1, highlightbackground=HACKER_BORDER)
        self.hitomi_output_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        
        browse_btn = tk.Button(output_frame, text="[ BROWSE ]", font=("Malgun Gothic", 12, "bold"), 
                             bg=HACKER_ACCENT, fg=HACKER_BG, relief="flat", 
                             activebackground=HACKER_GREEN, activeforeground=HACKER_BG, 
                             command=self.browse_output_dir_hitomi, cursor="hand2", 
                             borderwidth=1, highlightthickness=1, highlightbackground=HACKER_BORDER, 
                             padx=15, pady=5)
        browse_btn.pack(side="left")
        
        # Action buttons
        action_frame = tk.Frame(main_container, bg=HACKER_BG)
        action_frame.pack(fill="x", pady=(0, 15))
        
        self.hitomi_download_btn = tk.Button(action_frame, text="[ ⬇ DOWNLOAD ]", font=("Malgun Gothic", 12, "bold"), 
                                           width=15, bg=DOWNLOAD_BTN_COLOR, fg=HACKER_BG, relief="flat", 
                                           activebackground=DOWNLOAD_BTN_HOVER, activeforeground=HACKER_BG, 
                                           command=self.start_hitomi_download, cursor="hand2", 
                                           borderwidth=1, highlightthickness=1, highlightbackground=HACKER_BORDER, 
                                           padx=15, pady=5)
        self.hitomi_download_btn.pack(side="left", padx=(0, 10))
        
        self.hitomi_play_btn = tk.Button(action_frame, text="[ 📂 OPEN FOLDER ]", font=("Malgun Gothic", 12, "bold"), 
                                        bg=HACKER_ACCENT, fg=HACKER_BG, relief="flat", 
                                        activebackground=HACKER_GREEN, activeforeground=HACKER_BG, 
                                        command=self.open_download_folder_hitomi, cursor="hand2", 
                                        borderwidth=1, highlightthickness=1, highlightbackground=HACKER_BORDER, 
                                        padx=15, pady=5)
        self.hitomi_play_btn.pack(side="left", padx=(0, 10))
        
        # ZIP 압축 옵션 (customtkinter 스위치 스타일)
        zip_frame = tk.Frame(action_frame, bg=HACKER_BG)
        zip_frame.pack(side="left", padx=(0, 10))
        
        zip_label = tk.Label(zip_frame, text="[ ZIP 압축 ]", font=("Malgun Gothic", 12, "bold"), bg=HACKER_BG, fg=HACKER_GREEN)
        zip_label.pack(side="left", padx=(0, 10))
        
        # customtkinter 스위치 설정
        customtkinter.set_appearance_mode("dark")
        customtkinter.set_default_color_theme("green")
        
        self.zip_var = customtkinter.StringVar(value="off")
        self.switch = customtkinter.CTkSwitch(
            zip_frame,
            text="",
            command=self.toggle_switch,
            variable=self.zip_var,
            onvalue="on",
            offvalue="off",
            button_color=HACKER_GREEN,
            button_hover_color=HACKER_ACCENT,
            progress_color=HACKER_GREEN,
            fg_color=HACKER_DARK
        )
        self.switch.pack(side="left")
        
        # 스위치 상태 텍스트 제거
        self.switch_state_label = tk.Label(
            zip_frame,
            text="",
            font=("Malgun Gothic", 12),
            bg=HACKER_BG,
            fg=HACKER_RED
        )
        self.switch_state_label.pack(side="left", padx=(10, 0))
        
        # Log section
        log_section = tk.Frame(main_container, bg=HACKER_BG)
        log_section.pack(fill="both", expand=True, pady=(0, 15))
        
        log_label = tk.Label(log_section, text="[ 로그 ]", font=("Malgun Gothic", 12, "bold"), bg=HACKER_BG, fg=HACKER_GREEN)
        log_label.pack(anchor="w", pady=(0, 5))
        
        log_frame = tk.Frame(log_section, bg=HACKER_BG)
        log_frame.pack(fill="both", expand=True)
        
        self.hitomi_log_text = tk.Text(log_frame, width=90, height=10, font=("Consolas", 10), 
                                     bg=HACKER_DARK, fg=HACKER_GREEN, insertbackground=HACKER_GREEN, 
                                     relief="flat", wrap="word", highlightthickness=1, 
                                     highlightbackground=HACKER_BORDER)
        scrollbar = ttk.Scrollbar(log_frame, orient="vertical", command=self.hitomi_log_text.yview)
        
        self.hitomi_log_text.configure(yscrollcommand=scrollbar.set)
        self.hitomi_log_text.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Status and cancel button
        status_frame = tk.Frame(main_container, bg=HACKER_BG)
        status_frame.pack(fill="x", pady=(20, 10))
        
        separator = ttk.Separator(main_container, orient='horizontal')
        separator.pack(fill='x', pady=(0, 10))
        
        self.hitomi_status_var = tk.StringVar(value="[ 상태: 대기중 ]")
        self.hitomi_status_label = tk.Label(status_frame, textvariable=self.hitomi_status_var, anchor='w', font=("Malgun Gothic", 12), bg=HACKER_BG, fg=HACKER_GREEN)
        self.hitomi_status_label.pack(side="left", fill='x', expand=True)
        
        self.hitomi_cancel_button = tk.Button(status_frame, text="[ ⛔ CANCEL ]", font=("Malgun Gothic", 12), bg=HACKER_DARK, fg=HACKER_RED, relief="flat", activebackground=HACKER_RED, activeforeground=HACKER_BG, command=self.cancel_hitomi_download, state=tk.DISABLED, cursor="hand2", borderwidth=1, highlightthickness=1, highlightbackground=HACKER_BORDER)
        self.hitomi_cancel_button.pack(side="right", padx=10)

        # 개발자 정보 프레임
        dev_info_frame = tk.Frame(main_container, bg=HACKER_BG)
        dev_info_frame.pack(fill="x", pady=(0, 10))
        
        dev_info_label = tk.Label(dev_info_frame, text="이미지 다운로더(gallery-dl): @mikf | 영상 다운로더(yt-dlp): @yt-dlp | GUI 개발자: @noName_Come | 버전: V1.6", font=("Malgun Gothic", 10), bg=HACKER_BG, fg=HACKER_ACCENT)
        dev_info_label.pack(side="left", padx=10)
        
        # 첫 번째 URL 입력 필드 추가
        self.add_hitomi_url_field()

    def toggle_switch(self, event=None):
        """토글 스위치 상태 변경"""
        current_state = self.zip_var.get()
        if current_state == "on":
            self.switch_state_label.config(text="", fg=HACKER_GREEN)
        else:
            self.switch_state_label.config(text="", fg=HACKER_RED)

    def add_hitomi_url_field(self):
        row_frame = tk.Frame(self.hitomi_url_container, bg=HACKER_BG)
        row_frame.pack(fill="x", pady=(0, 2))

        entry_style = {
            "font": ("Malgun Gothic", 12),
            "bg": HACKER_DARK,
            "fg": HACKER_GREEN,
            "insertbackground": HACKER_GREEN,
            "highlightbackground": HACKER_DARK,
            "highlightcolor": HACKER_GREEN,
            "highlightthickness": 1,
            "insertwidth": 2,
            "relief": "flat",
            "width": 100,
            "bd": 0
        }

        url_entry = tk.Entry(row_frame, **entry_style)
        url_entry.insert(0, "URL 또는 번호를 입력하세요")
        url_entry.pack(side="top", fill="x", padx=0, ipady=5)

        def on_focus_in(event):
            self.clear_placeholder(url_entry, "URL 또는 번호를 입력하세요")

        def on_focus_out(event):
            self.restore_placeholder(url_entry, "URL 또는 번호를 입력하세요")
            self.convert_hitomi_number(url_entry)

        url_entry.bind("<FocusIn>", on_focus_in)
        url_entry.bind("<FocusOut>", on_focus_out)

        self.hitomi_url_sets.append((url_entry, None, row_frame))
        
        # URL 세트가 3개 이하일 때는 프레임 높이 조절
        hitomi_url_scroll_frame = self.hitomi_url_canvas.master
        
        if len(self.hitomi_url_sets) <= 3:
            new_height = 40 * len(self.hitomi_url_sets)  # 각 URL 세트당 40px
            hitomi_url_scroll_frame.configure(height=new_height)
            self.hitomi_url_scrollbar.pack_forget()  # 스크롤바 숨기기
        else:
            self.hitomi_url_scrollbar.pack(side="right", fill="y")  # 스크롤바 표시
        
        # Canvas 크기 업데이트
        self.hitomi_url_container.update_idletasks()
        self.hitomi_url_canvas.configure(scrollregion=self.hitomi_url_canvas.bbox("all"))

        # 마우스 스크롤 바인딩 추가
        self.hitomi_url_canvas.bind_all("<MouseWheel>", self._on_hitomi_mousewheel)

    def _on_hitomi_mousewheel(self, event):
        """히토미 탭 마우스 스크롤 이벤트 처리"""
        self.hitomi_url_canvas.yview_scroll(int(-1*(event.delta/120)), "units")

    def convert_hitomi_number(self, entry):
        """히토미 번호를 URL로 변환"""
        current_text = entry.get().strip()
        
        # 이미 URL 형식이면 변환하지 않음
        if current_text.startswith("https://hitomi.la/"):
            return
            
        # 플레이스홀더 텍스트면 무시
        if current_text == "URL 또는 번호를 입력하세요":
            return
            
        # 숫자만 입력된 경우 URL로 변환
        if current_text.isdigit():
            url = f"https://hitomi.la/galleries/{current_text}.html"
            entry.delete(0, tk.END)
            entry.insert(0, url)
            self.thread_safe_log_hitomi(f"✅ 번호 {current_text}가 URL로 자동 변환되었습니다.")

    def remove_hitomi_url_field(self):
        """히토미 탭에서 URL 입력 필드 제거"""
        if len(self.hitomi_url_sets) > 1:
            _, _, row_frame = self.hitomi_url_sets.pop()
            row_frame.destroy()

            # URL 세트가 3개 이하일 때 프레임 높이 조절
            hitomi_url_scroll_frame = self.hitomi_url_canvas.master
            scrollbar = [child for child in hitomi_url_scroll_frame.winfo_children() if isinstance(child, ttk.Scrollbar)][0]
            
            if len(self.hitomi_url_sets) <= 3:
                new_height = 40 * len(self.hitomi_url_sets)  # 각 URL 세트당 40px
                hitomi_url_scroll_frame.configure(height=new_height)
                scrollbar.pack_forget()  # 스크롤바 숨기기
            else:
                scrollbar.pack(side="right", fill="y")  # 스크롤바 표시

            # Canvas 크기 업데이트
            self.hitomi_url_container.update_idletasks()
            self.hitomi_url_canvas.configure(scrollregion=self.hitomi_url_canvas.bbox("all"))

    def clear_all_hitomi_urls(self):
        """히토미 탭의 모든 URL 입력 필드 초기화"""
        for url_entry, _, _ in self.hitomi_url_sets:
            url_entry.delete(0, tk.END)
            url_entry.insert(0, "URL 또는 번호를 입력하세요")

        while len(self.hitomi_url_sets) > 1:
            _, _, row_frame = self.hitomi_url_sets.pop()
            row_frame.destroy()

        # 프레임 크기를 초기 크기로 복원
        hitomi_url_scroll_frame = self.hitomi_url_canvas.master
        hitomi_url_scroll_frame.configure(height=40)
        self.hitomi_url_scrollbar.pack_forget()  # 스크롤바 숨기기
        
        # Canvas 크기 업데이트
        self.hitomi_url_container.update_idletasks()
        self.hitomi_url_canvas.configure(scrollregion=self.hitomi_url_canvas.bbox("all"))

    def start_hitomi_download(self):
        """히토미 다운로드 시작"""
        url_info = []
        self._cancel_requested = False

        for url_entry, _, _ in self.hitomi_url_sets:
            url = url_entry.get().strip()

            # URL 입력창이 비어있지 않고 플레이스홀더가 아닌 경우
            if url != "URL 또는 번호를 입력하세요" and url:
                # YouTube URL 체크
                if is_youtube(url):
                    self.thread_safe_log_hitomi(f"⚠ YouTube URL이 감지되었습니다: {url}")
                    self.thread_safe_log_hitomi("→ 유튜브 다운로더 탭으로 이동하여 다운로드해주세요.")
                    self.show_tab(self.ytdlp_frame)
                    return
                
                # Kemono URL 체크
                if "kemono.su" in url or "kemono.party" in url:
                    self.thread_safe_log_hitomi(f"⚠ Kemono URL이 감지되었습니다: {url}")
                    self.thread_safe_log_hitomi("→ KEMONOPARTY 다운로더 탭으로 이동하여 다운로드해주세요.")
                    self.show_tab(self.gallery_dl_frame)
                    return
                
                # 히토미 URL이 아닌 경우
                if not url.startswith("https://hitomi.la/") and not url.isdigit():
                    self.thread_safe_log_hitomi(f"⚠ 잘못된 URL 형식입니다: {url}")
                    self.thread_safe_log_hitomi("→ 히토미 URL 또는 작품 번호만 입력해주세요.")
                    return

                # 숫자만 입력된 경우 URL로 변환
                if url.isdigit():
                    url = f"https://hitomi.la/galleries/{url}.html"
                
                url_info.append((url, None))

        if not url_info:
            try:
                clip = self.root.clipboard_get().strip()
                # YouTube URL 체크
                if is_youtube(clip):
                    self.thread_safe_log_hitomi("⚠ 클립보드의 URL이 YouTube 링크입니다.")
                    self.thread_safe_log_hitomi("→ 유튜브 다운로더 탭으로 이동하여 다운로드해주세요.")
                    self.show_tab(self.ytdlp_frame)
                    return
                
                # Kemono URL 체크
                if "kemono.su" in clip or "kemono.party" in clip:
                    self.thread_safe_log_hitomi("⚠ 클립보드의 URL이 Kemono 링크입니다.")
                    self.thread_safe_log_hitomi("→ KEMONOPARTY 다운로더 탭으로 이동하여 다운로드해주세요.")
                    self.show_tab(self.gallery_dl_frame)
                    return

                # 클립보드의 내용이 숫자인 경우 URL로 변환
                if clip.isdigit():
                    clip = f"https://hitomi.la/galleries/{clip}.html"
                if clip.startswith("https://hitomi.la/"):
                    url_info.append((clip, None))
                else:
                    raise ValueError
            except:
                messagebox.showerror("오류", "URL이나 히토미 번호를 입력하거나 클립보드에 유효한 히토미 링크가 있어야 합니다.")
                return

        output_dir = self.hitomi_output_dir_var.get().strip()
        self.store_output_dir(output_dir)
        
        self.disable_hitomi_ui()
        self.hitomi_status_var.set("[ 상태: 다운로드 중 ]")
        self.thread_safe_log_hitomi("다운로드를 시작합니다...")
        
        threading.Thread(target=self.download_multiple_hitomi, args=(url_info, output_dir), daemon=True).start()

    def download_multiple_hitomi(self, url_info_list, output_dir):
        """여러 히토미 URL 다운로드"""
        failed_urls = []
        total_urls = len(url_info_list)

        try:
            # hitomi 폴더 생성
            hitomi_dir = os.path.join(output_dir, "hitomi")
            os.makedirs(hitomi_dir, exist_ok=True)

            for idx, (url, filename) in enumerate(url_info_list, start=1):
                if self._cancel_requested:  # 취소 요청 확인
                    self.thread_safe_log_hitomi("⛔ 다운로드가 취소되었습니다.")
                    break

                self.hitomi_status_var.set(f"[ 상태: 다운로드 중 ({idx}/{total_urls}) ]")
                self.thread_safe_log_hitomi(f"🔄 다운로드 시작: {url}")
                
                if not url.startswith("https://hitomi.la/"):
                    self.thread_safe_log_hitomi(f"⚠ 히토미 URL이 아닙니다: {url}")
                    failed_urls.append(url)
                    continue
                
                try:
                    # gallery-dl 다운로드 시도 (사용자가 지정한 hitomi 폴더 사용)
                    result = gallery_download(
                        url=url,
                        output_dir=hitomi_dir,  # 사용자가 지정한 hitomi 폴더 사용
                        filename=filename,
                        selected_exts=None,  # 모든 파일 다운로드
                        log_func=self.thread_safe_log_hitomi,
                        status_func=lambda msg: self.hitomi_status_var.set(f"[ 상태: {msg} ]"),
                        cancel_check_func=lambda: self._cancel_requested,  # 취소 확인 함수
                        proc_register=self.processes.append
                    )

                    # 다운로드 결과 처리
                    # gallery_download 함수는 성공 시 True 또는 다운로드 경로를 반환할 수 있음
                    if result is True or (isinstance(result, str) and result):
                        self.thread_safe_log_hitomi(f"✅ 완료: {url}")
                        
                        # ZIP 압축 옵션이 활성화된 경우
                        if self.zip_var.get() == "on":
                            try:
                                # 가장 최근에 수정된 폴더 찾기
                                latest_folder = None
                                latest_mtime = 0
                                
                                for folder in os.listdir(hitomi_dir):
                                    folder_path = os.path.join(hitomi_dir, folder)
                                    if os.path.isdir(folder_path):
                                        mtime = os.path.getmtime(folder_path)
                                        if mtime > latest_mtime:
                                            latest_mtime = mtime
                                            latest_folder = folder_path
                                
                                if latest_folder:
                                    # ZIP 파일명 설정 (폴더 이름 사용)
                                    folder_name = os.path.basename(latest_folder)
                                    zip_filename = f"{folder_name}.zip"
                                    zip_path = os.path.join(hitomi_dir, zip_filename)  # hitomi 폴더 안에 ZIP 파일 저장
                                    
                                    # ZIP 압축
                                    self.thread_safe_log_hitomi("📦 ZIP 압축 시작...")
                                    import zipfile
                                    import time
                                    
                                    # 파일이 완전히 저장될 때까지 잠시 대기
                                    time.sleep(2)
                                    
                                    try:
                                        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                                            for root, _, files in os.walk(latest_folder):
                                                for file in files:
                                                    file_path = os.path.join(root, file)
                                                    arcname = os.path.relpath(file_path, latest_folder)
                                                    try:
                                                        zipf.write(file_path, arcname)
                                                    except PermissionError:
                                                        self.thread_safe_log_hitomi(f"⚠ 파일 액세스 오류: {file_path}")
                                                        continue
                                        
                                        # 원본 폴더 삭제 시도
                                        try:
                                            import shutil
                                            shutil.rmtree(latest_folder)
                                            self.thread_safe_log_hitomi("✅ ZIP 압축 완료")
                                        except PermissionError:
                                            self.thread_safe_log_hitomi("⚠ 원본 폴더 삭제 실패: 파일이 사용 중입니다")
                                    except Exception as e:
                                        self.thread_safe_log_hitomi(f"⚠ ZIP 압축 중 오류 발생: {str(e)}")
                                else:
                                    self.thread_safe_log_hitomi("⚠ 다운로드된 폴더를 찾을 수 없습니다.")
                            except Exception as e:
                                self.thread_safe_log_hitomi(f"⚠ ZIP 압축 실패: {str(e)}")
                    else:
                        self.thread_safe_log_hitomi(f"❌ 실패: {url}")
                        failed_urls.append(url)
                        
                except Exception as e:
                    self.thread_safe_log_hitomi(f"❌ 오류 발생: {str(e)}")
                    failed_urls.append(url)

            if not self._cancel_requested:  # 취소되지 않은 경우에만 결과 표시
                if failed_urls:
                    self.thread_safe_log_hitomi("🚫 다음 URL에서 실패했습니다:")
                    for f in failed_urls:
                        self.thread_safe_log_hitomi(f"    - {f}")
                    self.hitomi_status_var.set("[ 상태: 일부 실패 ]")
                else:
                    self.hitomi_status_var.set("[ 상태: 완료 ]")
                    self.thread_safe_log_hitomi("✅ 모든 다운로드가 완료되었습니다!")
        finally:
            self.root.after(0, self.enable_hitomi_ui)

    def cancel_hitomi_download(self):
        """히토미 다운로드 취소"""
        self._cancel_requested = True  # 취소 플래그 설정
        self.hitomi_cancel_button.config(state="disabled")
        self.hitomi_status_var.set("[ 상태: 취소 중 ]")
        self.log_hitomi("⛔ 취소 요청됨 → 다운로드를 중지합니다...")
        
        for proc in self.processes:
            try:
                if os.name == "nt":
                    kill_proc_tree(proc.pid)
                else:
                    proc.terminate()
            except:
                pass
                
        self.processes.clear()
        self.enable_hitomi_ui()

    def disable_hitomi_ui(self):
        """히토미 UI 비활성화"""
        self.hitomi_download_btn.config(state="disabled")
        self.hitomi_cancel_button.config(state="normal")
        self.add_hitomi_url_btn.config(state="disabled")
        self.remove_hitomi_url_btn.config(state="disabled")
        self.clear_hitomi_url_btn.config(state="disabled")
        
        # URL 입력 필드들 비활성화
        for url_entry, _, _ in self.hitomi_url_sets:
            url_entry.config(state="disabled")
            
        self.hitomi_output_entry.config(state="disabled")

    def enable_hitomi_ui(self):
        """히토미 UI 활성화"""
        self.hitomi_download_btn.config(state="normal")
        self.hitomi_cancel_button.config(state="disabled")
        self.add_hitomi_url_btn.config(state="normal")
        self.remove_hitomi_url_btn.config(state="normal")
        self.clear_hitomi_url_btn.config(state="normal")
        
        # URL 입력 필드들 활성화
        for url_entry, _, _ in self.hitomi_url_sets:
            url_entry.config(state="normal")
            
        self.hitomi_output_entry.config(state="normal")
        self._cancel_requested = False
        self.hitomi_status_var.set("[ 상태: 대기중 ]")

    def thread_safe_log_hitomi(self, msg):
        """스레드 안전한 히토미 로그 출력"""
        if self and self.hitomi_log_text and msg:
            self.root.after(0, lambda: self._append_hitomi_log(msg))

    def _append_hitomi_log(self, msg):
        """히토미 로그 메시지 추가"""
        try:
            self.hitomi_log_text.config(state="normal")
            self.hitomi_log_text.insert(tk.END, f"{msg}\n")
            self.hitomi_log_text.see(tk.END)
            self.hitomi_log_text.config(state="disabled")
        except Exception as e:
            print(f"로그 출력 오류: {e}")

    def browse_output_dir_hitomi(self):
        """히토미 다운로더의 출력 디렉토리 선택"""
        dir = filedialog.askdirectory(initialdir=self.hitomi_output_dir_var.get())
        if dir:
            self.hitomi_output_dir_var.set(dir)
            self.store_output_dir(dir)

    def open_download_folder_hitomi(self):
        """히토미 다운로드 폴더 열기"""
        base_folder = self.hitomi_output_dir_var.get().strip()
        hitomi_folder = os.path.join(base_folder, "hitomi")
        
        if os.path.exists(hitomi_folder):
            try:
                os.startfile(hitomi_folder)
            except Exception as e:
                messagebox.showerror("오류", f"폴더 열기 실패:\n{e}")
        else:
            messagebox.showwarning("경고", "hitomi 폴더가 존재하지 않습니다.")

    def create_common_button(self, parent, text, command, is_download=False, is_cancel=False):
        """공통 버튼 생성 헬퍼 메서드"""
        bg_color = DOWNLOAD_BTN_COLOR if is_download else (HACKER_DARK if is_cancel else HACKER_ACCENT)
        hover_color = DOWNLOAD_BTN_HOVER if is_download else (HACKER_RED if is_cancel else HACKER_GREEN)
        fg_color = HACKER_BG
        
        return tk.Button(
            parent,
            text=text,
            font=("Malgun Gothic", 12, "bold"),
            bg=bg_color,
            fg=fg_color,
            relief="flat",
            activebackground=hover_color,
            activeforeground=HACKER_BG,
            command=command,
            cursor="hand2",
            borderwidth=1,
            highlightthickness=1,
            highlightbackground=HACKER_BORDER,
            padx=15,
            pady=5
        )

    def create_common_entry(self, parent, placeholder, width=None):
        """공통 입력 필드 생성 헬퍼 메서드"""
        entry = tk.Entry(
            parent,
            font=("Malgun Gothic", 12),
            bg=HACKER_DARK,
            fg=HACKER_GREEN,
            insertbackground=HACKER_GREEN,
            relief="flat",
            highlightthickness=1,
            highlightbackground=HACKER_BORDER,
            width=width
        )
        entry.insert(0, placeholder)
        entry.bind("<FocusIn>", lambda e: self.clear_placeholder(entry, placeholder))
        entry.bind("<FocusOut>", lambda e: self.restore_placeholder(entry, placeholder))
        return entry

    def create_common_label(self, parent, text, is_title=False):
        """공통 레이블 생성 헬퍼 메서드"""
        return tk.Label(
            parent,
            text=text,
            font=("Malgun Gothic", 16 if is_title else 12, "bold"),
            bg=HACKER_BG,
            fg=HACKER_GREEN
        )

    def create_common_log_area(self, parent):
        """공통 로그 영역 생성 헬퍼 메서드"""
        log_frame = tk.Frame(parent, bg=HACKER_BG)
        log_frame.pack(fill="both", expand=True)
        
        log_text = tk.Text(
            log_frame,
            width=90,
            height=10,
            font=("Consolas", 10),
            bg=HACKER_DARK,
            fg=HACKER_GREEN,
            insertbackground=HACKER_GREEN,
            relief="flat",
            wrap="word",
            highlightthickness=1,
            highlightbackground=HACKER_BORDER
        )
        
        scrollbar = ttk.Scrollbar(log_frame, orient="vertical", command=log_text.yview)
        log_text.configure(yscrollcommand=scrollbar.set)
        
        log_text.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        return log_text

    def create_common_status_frame(self, parent, status_var, cancel_command):
        """공통 상태 프레임 생성 헬퍼 메서드"""
        status_frame = tk.Frame(parent, bg=HACKER_BG)
        status_frame.pack(fill="x", pady=(20, 10))
        
        separator = ttk.Separator(parent, orient='horizontal')
        separator.pack(fill='x', pady=(0, 10))
        
        status_label = tk.Label(
            status_frame,
            textvariable=status_var,
            anchor='w',
            font=("Malgun Gothic", 12),
            bg=HACKER_BG,
            fg=HACKER_GREEN
        )
        status_label.pack(side="left", fill='x', expand=True)
        
        cancel_button = self.create_common_button(
            status_frame,
            "[ ⛔ CANCEL ]",
            cancel_command,
            is_cancel=True
        )
        cancel_button.pack(side="right", padx=10)
        cancel_button.config(state=tk.DISABLED)
        
        return status_label, cancel_button