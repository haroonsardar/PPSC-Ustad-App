import json
import random
import os
import re

class PPSCLogic:
    def __init__(self):
        self.data_path = 'data/papers.json'
        self.bookmark_path = 'data/bookmarks.json'
        self.history_path = 'data/history.json'
        
        self.papers = []
        self.bookmarks = []
        self.history = []
        
        self.load_data()
        self.load_bookmarks()
        self.load_history()

    # --- LOAD DATA ---
    def load_data(self):
        if os.path.exists(self.data_path):
            try:
                with open(self.data_path, 'r') as f: self.papers = json.load(f)
            except: self.papers = []
        else: self.papers = []

    def load_bookmarks(self):
        if os.path.exists(self.bookmark_path):
            try:
                with open(self.bookmark_path, 'r') as f: self.bookmarks = json.load(f)
            except: self.bookmarks = []
        else: self.bookmarks = []

    def load_history(self):
        if os.path.exists(self.history_path):
            try:
                with open(self.history_path, 'r') as f: self.history = json.load(f)
            except: self.history = []
        else: self.history = []

    # --- SAVE DATA ---
    def save_data(self):
        with open(self.data_path, 'w') as f: json.dump(self.papers, f, indent=4)
    def save_bookmarks(self):
        with open(self.bookmark_path, 'w') as f: json.dump(self.bookmarks, f, indent=4)
    def save_history(self):
        with open(self.history_path, 'w') as f: json.dump(self.history, f, indent=4)

    # --- PAPER PARSER ---
    def add_new_paper(self, title, raw_text):
        new_questions = []
        lines = [line.strip() for line in raw_text.split('\n') if line.strip()]
        current_q = {}
        current_options = []
        
        Q_PATTERN = r'^(Q\s*\d*[:.)]|Q\.|[0-9]+[:.)])'
        OPT_PATTERN = r'^([A-D]|[a-d])[:.)]\s*'
        
        for line in lines:
            if "Part" in line and ":" in line and len(line) < 40: continue

            if re.match(Q_PATTERN, line, re.IGNORECASE):
                if 'q' in current_q: self._finalize_question(current_q, current_options, new_questions)
                current_q = {'q': re.sub(Q_PATTERN, '', line, flags=re.IGNORECASE).strip(), 'id': len(new_questions) + 1}
                current_options = []
            elif re.match(OPT_PATTERN, line):
                current_options.append(re.sub(OPT_PATTERN, '', line).strip())
            elif "CORRECT" in line.upper() or "ANSWER" in line.upper() or "ANS:" in line.upper():
                match = re.search(r'\b([A-D])\b', line.upper())
                if match: current_q['correct_key'] = match.group(1)

        if 'q' in current_q: self._finalize_question(current_q, current_options, new_questions)

        if new_questions:
            self.papers.append({"id": random.randint(10000, 99999), "title": title, "questions": new_questions})
            self.save_data()
            return len(new_questions)
        return 0

    def _finalize_question(self, q_dict, options, q_list):
        if len(options) < 2 or 'correct_key' not in q_dict: return
        mapping = {'A': 0, 'B': 1, 'C': 2, 'D': 3}
        key = q_dict['correct_key']
        if key in mapping and len(options) > mapping[key]:
            q_dict['options'] = options
            q_dict['correct'] = options[mapping[key]]
            del q_dict['correct_key']
            q_list.append(q_dict)

    def get_questions_from_selected_papers(self, selected_indices, limit=20):
        pool = []
        for index in selected_indices:
            if 0 <= index < len(self.papers): pool.extend(self.papers[index]['questions'])
        if not pool: return []
        random.shuffle(pool)
        return pool[:limit]

    def search_questions(self, query):
        query = query.lower().strip()
        if not query: return []
        results = []
        for paper in self.papers:
            for q in paper['questions']:
                if query in q['q'].lower():
                    results.append({'paper_title': paper['title'], 'q': q['q'], 'correct': q['correct']})
        return results

    # --- FEATURES ---
    def toggle_bookmark(self, question_data):
        found = False
        for i, b in enumerate(self.bookmarks):
            if b['q'] == question_data['q']:
                self.bookmarks.pop(i); found = True; break
        if not found: self.bookmarks.append(question_data)
        self.save_bookmarks()
        return not found

    def is_bookmarked(self, q_text):
        for b in self.bookmarks:
            if b['q'] == q_text: return True
        return False

    def add_exam_result(self, score, total, percentage):
        self.history.append({"score": score, "total": total, "percentage": percentage})
        if len(self.history) > 10: self.history.pop(0)
        self.save_history()