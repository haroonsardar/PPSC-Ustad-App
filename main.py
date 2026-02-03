from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen
from kivymd.uix.button import MDFillRoundFlatButton
from kivymd.uix.list import OneLineAvatarIconListItem, IconRightWidget, OneLineListItem, TwoLineListItem, ThreeLineListItem
from kivymd.uix.textfield import MDTextField
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.dialog import MDDialog
from kivymd.uix.progressbar import MDProgressBar
from kivy.lang import Builder
from kivymd.toast import toast
from kivy.clock import Clock
from kivy.core.audio import SoundLoader
from logic import PPSCLogic

# TTS Check
try:
    import pyttsx3
    HAS_TTS = True
    engine = pyttsx3.init()
except ImportError:
    HAS_TTS = False

# Screens
class HomeScreen(MDScreen): pass
class AddPaperScreen(MDScreen): pass
class ExamConfigScreen(MDScreen): pass
class ExamScreen(MDScreen): pass
class ResultScreen(MDScreen): pass
class StudyScreen(MDScreen): pass
class SearchScreen(MDScreen): pass
class ReviewScreen(MDScreen): pass
class BookmarksScreen(MDScreen): pass
class StatsScreen(MDScreen): pass

# Safe Selection Item
class PaperSelectionItem(OneLineAvatarIconListItem):
    def __init__(self, paper_index, paper_title, app_ref, **kwargs):
        super().__init__(**kwargs)
        self.text = paper_title
        self.paper_index = paper_index
        self.app = app_ref
        self.right_icon = IconRightWidget(icon="checkbox-marked")
        self.right_icon.disabled = True 
        self.add_widget(self.right_icon)
        self.is_selected = True
        self.update_ui()
    def on_release(self):
        self.is_selected = not self.is_selected
        self.update_ui()
        self.app.update_tracker(self.paper_index, self.is_selected)
    def update_ui(self):
        if self.is_selected:
            self.right_icon.icon = "checkbox-marked"
            self.right_icon.theme_text_color = "Custom"
            self.right_icon.text_color = (0, 0.5, 0.5, 1) 
        else:
            self.right_icon.icon = "checkbox-blank-outline"
            self.right_icon.theme_text_color = "Secondary"

class PPSCApp(MDApp):
    def build(self):
        self.theme_cls.primary_palette = "Teal"
        self.theme_cls.primary_hue = "700"
        self.theme_cls.theme_style = "Light"
        self.title = "PPSC Ustad"
        
        self.logic = PPSCLogic()
        self.current_exam_qs = []
        self.current_q_index = 0
        self.score = 0.0
        self.correct_count = 0
        self.wrong_count = 0
        self.selected_indices = set()
        self.answer_locked = False
        self.wrong_answers = [] 
        
        # Sounds
        self.sound_correct = SoundLoader.load('assets/correct.wav')
        self.sound_wrong = SoundLoader.load('assets/wrong.wav')
        
        self.timer_event = None
        self.time_left = 55
        self.limit_field = None 
        
        return Builder.load_file('style.kv')

    # --- ABOUT DIALOG (UPDATED) ---
    def show_about(self):
        self.dialog = MDDialog(
            title="About PPSC Ustad",
            text="Developed by: Haroon Khan\nVersion: Final Pro",
            radius=[20, 7, 20, 7],
        )
        self.dialog.open()

    # --- FEATURES ---
    def speak_question(self):
        if HAS_TTS:
            import threading
            threading.Thread(target=lambda: (engine.say(self.current_exam_qs[self.current_q_index]['q']), engine.runAndWait())).start()
        else: toast("Install pyttsx3")

    def toggle_current_bookmark(self):
        if not self.current_exam_qs: return
        is_saved = self.logic.toggle_bookmark(self.current_exam_qs[self.current_q_index])
        self.update_bookmark_icon()
        toast("Saved" if is_saved else "Removed")

    def update_bookmark_icon(self):
        btn = self.root.get_screen('exam').ids.bookmark_btn
        q_text = self.current_exam_qs[self.current_q_index]['q']
        if self.logic.is_bookmarked(q_text):
            btn.icon = "heart"; btn.text_color = (1, 0, 0, 1)
        else:
            btn.icon = "heart-outline"; btn.text_color = (1, 1, 1, 1)

    def go_home(self): self.stop_timer(); self.root.current = 'home'
    def go_to_result(self): self.root.current = 'result'
    def update_tracker(self, index, is_added):
        if is_added: self.selected_indices.add(index)
        else: self.selected_indices.discard(index)

    # --- DATA LISTS ---
    def prepare_bookmarks(self):
        screen = self.root.get_screen('bookmarks')
        screen.ids.bookmarks_list.clear_widgets()
        if not self.logic.bookmarks: screen.ids.bookmarks_list.add_widget(OneLineListItem(text="No saved questions."))
        for b in self.logic.bookmarks:
            screen.ids.bookmarks_list.add_widget(ThreeLineListItem(text=f"{b['q']}", secondary_text=f"Ans: {b['correct']}", tertiary_text="Tap to remove", on_release=lambda x, q=b: self.remove_bm(q)))
        self.root.current = 'bookmarks'
    def remove_bm(self, q): self.logic.toggle_bookmark(q); self.prepare_bookmarks()

    def prepare_stats(self):
        screen = self.root.get_screen('stats')
        screen.ids.stats_list.clear_widgets()
        if not self.logic.history: screen.ids.stats_list.add_widget(OneLineListItem(text="No history yet."))
        for h in reversed(self.logic.history):
            box = MDBoxLayout(orientation='vertical', size_hint_y=None, height="60dp", padding="5dp")
            box.add_widget(OneLineListItem(text=f"Score: {h['score']:.2f} / {h['total']}"))
            pb = MDProgressBar(value=h['percentage'], size_hint_y=None, height="8dp")
            pb.color = (0, 0.7, 0, 1) if h['percentage'] >= 50 else (0.9, 0, 0, 1)
            box.add_widget(pb)
            screen.ids.stats_list.add_widget(box)
        self.root.current = 'stats'

    def prepare_study_mode(self):
        screen = self.root.get_screen('study')
        screen.ids.study_list.clear_widgets()
        if not self.logic.papers: return
        for p in self.logic.papers:
            screen.ids.study_list.add_widget(OneLineAvatarIconListItem(text=f"📂 {p['title']}", bg_color=(0.92, 0.96, 0.96, 1)))
            for q in p['questions']:
                screen.ids.study_list.add_widget(TwoLineListItem(text=f"Q: {q['q']}", secondary_text=f"Ans: {q['correct']}"))
        self.root.current = 'study'

    def prepare_search_mode(self):
        self.root.get_screen('search').ids.search_field.text = ""
        self.root.get_screen('search').ids.search_results_list.clear_widgets()
        self.root.current = 'search'

    def perform_search(self, query):
        res_list = self.root.get_screen('search').ids.search_results_list
        res_list.clear_widgets()
        results = self.logic.search_questions(query)
        if not results: res_list.add_widget(OneLineListItem(text="No results."))
        else:
            for r in results:
                res_list.add_widget(ThreeLineListItem(text=f"Q: {r['q']}", secondary_text=f"Ans: {r['correct']}", tertiary_text=f"Src: {r['paper_title']}"))

    def prepare_exam_config(self):
        screen = self.root.get_screen('exam_config')
        screen.ids.paper_selection_list.clear_widgets()
        self.selected_indices = set()
        box = MDBoxLayout(orientation='vertical', size_hint_y=None, height="80dp", padding=[0, 0, 0, 10])
        self.limit_field = MDTextField(hint_text="Questions Limit (Default: 20)", input_filter="int", mode="rectangle")
        box.add_widget(self.limit_field)
        screen.ids.paper_selection_list.add_widget(box)
        if not self.logic.papers: toast("No papers!")
        for i, p in enumerate(self.logic.papers):
            self.selected_indices.add(i)
            screen.ids.paper_selection_list.add_widget(PaperSelectionItem(paper_index=i, paper_title=p['title'], app_ref=self))
        self.root.current = 'exam_config'

    def start_exam(self):
        if not self.selected_indices: toast("Select a paper!"); return
        limit = 20
        if self.limit_field and self.limit_field.text: limit = int(self.limit_field.text)
        self.current_exam_qs = self.logic.get_questions_from_selected_papers(list(self.selected_indices), limit)
        if not self.current_exam_qs: toast("Error!"); return
        self.current_q_index = 0; self.score = 0.0; self.correct_count = 0; self.wrong_count = 0; self.wrong_answers = []
        self.load_question_ui()
        self.root.current = 'exam'

    def load_question_ui(self):
        screen = self.root.get_screen('exam')
        self.answer_locked = False
        if self.current_q_index >= len(self.current_exam_qs): self.show_results(); return
        q = self.current_exam_qs[self.current_q_index]
        screen.ids.question_text.text = q['q']
        screen.ids.next_btn.disabled = False
        screen.ids.progress_label.text = f"{self.current_q_index + 1} / {len(self.current_exam_qs)}"
        self.update_bookmark_icon()
        box = screen.ids.options_box; box.clear_widgets()
        for opt in q['options']:
            btn = MDFillRoundFlatButton(text=opt, size_hint_x=1, md_bg_color=(0.93, 0.93, 0.93, 1), text_color=(0, 0, 0, 1))
            btn.bind(on_release=lambda x, o=opt: self.check_answer(x, o, q['correct']))
            box.add_widget(btn)
        self.start_timer()

    def check_answer(self, btn, selected, correct):
        if self.answer_locked: return
        self.stop_timer(); self.answer_locked = True
        if selected == correct:
            if self.sound_correct: self.sound_correct.play()
            btn.md_bg_color = (0, 0.8, 0, 1); btn.text_color = (1, 1, 1, 1)
            self.score += 1; self.correct_count += 1
        else:
            if self.sound_wrong: self.sound_wrong.play()
            btn.md_bg_color = (0.9, 0, 0, 1); btn.text_color = (1, 1, 1, 1)
            self.score -= 0.25; self.wrong_count += 1
            self.wrong_answers.append({'q': self.current_exam_qs[self.current_q_index]['q'], 'selected': selected, 'correct': correct})
            for child in self.root.get_screen('exam').ids.options_box.children:
                if child.text == correct: child.md_bg_color = (0, 0.8, 0, 1); child.text_color = (1, 1, 1, 1)

    def next_question(self):
        if not self.answer_locked: self.stop_timer()
        self.current_q_index += 1; self.load_question_ui()

    def start_timer(self):
        self.stop_timer(); self.time_left = 55; self.update_timer_label()
        self.timer_event = Clock.schedule_interval(lambda dt: self.tick_timer(), 1)
    def stop_timer(self):
        if self.timer_event: self.timer_event.cancel(); self.timer_event = None
    def tick_timer(self):
        self.time_left -= 1; self.update_timer_label()
        if self.time_left <= 0: self.handle_timeout()
    def update_timer_label(self):
        self.root.get_screen('exam').ids.timer_label.text = f"{self.time_left}s"
    def handle_timeout(self):
        self.stop_timer(); toast("Time Up!")
        self.answer_locked = True
        q = self.current_exam_qs[self.current_q_index]
        self.wrong_answers.append({'q': q['q'], 'selected': "Timeout", 'correct': q['correct']})
        for child in self.root.get_screen('exam').ids.options_box.children:
            if child.text == q['correct']: child.md_bg_color = (0, 0.8, 0, 1); child.text_color = (1, 1, 1, 1)

    def show_results(self):
        self.stop_timer()
        screen = self.root.get_screen('result')
        total = len(self.current_exam_qs)
        final = max(0, self.score)
        pct = int((final / total) * 100) if total > 0 else 0
        screen.ids.score_label.text = f"{final:.2f} / {total} ({pct}%)"
        screen.ids.stats_label.text = f"Correct: {self.correct_count} | Wrong: {self.wrong_count}"
        self.logic.add_exam_result(final, total, pct)
        self.root.current = 'result'

    def prepare_review_mode(self):
        screen = self.root.get_screen('review')
        screen.ids.review_list.clear_widgets()
        for w in self.wrong_answers:
            screen.ids.review_list.add_widget(ThreeLineListItem(text=f"{w['q']}", secondary_text=f"❌ You: {w['selected']}", tertiary_text=f"✅ Correct: {w['correct']}", bg_color=(0.98, 0.9, 0.9, 1)))
        self.root.current = 'review'

    def save_paper_from_ui(self):
        screen = self.root.get_screen('add_paper')
        if screen.ids.paper_title.text and screen.ids.raw_text.text:
            self.logic.add_new_paper(screen.ids.paper_title.text, screen.ids.raw_text.text)
            toast("Saved!"); self.go_home()
        else: toast("Fill Data")

if __name__ == '__main__':
    PPSCApp().run()