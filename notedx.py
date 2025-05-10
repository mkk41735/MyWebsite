import os
import tkinter as tk
from tkinter import messagebox, filedialog, simpledialog
from fpdf import FPDF
import platform
import tempfile
import subprocess
import threading
import time
import shutil

# إعداد مجلد الحفظ الرئيسي
NOTES_DIR = "NOTEDX_Notes"
os.makedirs(NOTES_DIR, exist_ok=True)

# تطبيق FPDF مخصص للغة العربية
class ArabicPDF(FPDF):
    def __init__(self):
        super().__init__()
        font_path = os.path.join(os.path.dirname(__file__), "Amiri-Regular.ttf")
        if not os.path.exists(font_path):
            messagebox.showerror("خطأ", f"لم يتم العثور على الخط: {font_path}.")
        self.add_font('Amiri', '', font_path, uni=True)
        self.set_font('Amiri', '', 14)

    def header(self):
        self.set_font('Amiri', 'B', 12)
        self.cell(0, 10, 'NOTEDX - ملاحظاتك', 0, 1, 'C')

    def footer(self):
        self.set_y(-15)
        self.set_font('Amiri', 'I', 10)
        self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')

# التطبيق الرئيسي
class NotedxApp:
    def __init__(self, root):
        self.root = root
        self.root.title("NOTEDX - تطبيق الملاحظات")
        self.root.geometry("1000x600")
        self.root.configure(bg="#2b2b2b")

        self.sections = []
        self.current_section = None
        self.current_note_path = None
        self.password_set = False
        self.password = None

        self.create_ui()
        self.load_sections()
        self.bind_shortcuts()

    def create_ui(self):
        # الإطارات الرئيسية
        self.left_frame = tk.Frame(self.root, bg="#333")
        self.left_frame.pack(side="left", fill="y")
        self.right_frame = tk.Frame(self.root, bg="#2b2b2b")
        self.right_frame.pack(side="right", fill="both", expand=True)
        self.bottom_frame = tk.Frame(self.root, bg="#1e1e1e")
        self.bottom_frame.pack(side="bottom", fill="x")

        # قائمة الأقسام
        tk.Label(self.left_frame, text="الأقسام", bg="#333", fg="white", font=("Arial", 14)).pack(pady=5)
        self.section_listbox = tk.Listbox(self.left_frame, width=25, bg="#444", fg="white")
        self.section_listbox.pack(padx=10, pady=5)
        self.section_listbox.bind("<<ListboxSelect>>", self.on_section_select)

        # أزرار الأقسام
        tk.Button(self.left_frame, text="إضافة قسم", command=self.add_section, bg="#444", fg="white").pack(pady=5)
        tk.Button(self.left_frame, text="حذف قسم", command=self.delete_section, bg="#444", fg="white").pack(pady=5)
        tk.Button(self.left_frame, text="إعداد كلمة مرور", command=self.set_password, bg="#444", fg="white").pack(pady=5)

        # قائمة الملاحظات
        self.note_listbox = tk.Listbox(self.left_frame, width=25, bg="#444", fg="white")
        self.note_listbox.pack(padx=10, pady=10)
        self.note_listbox.bind("<<ListboxSelect>>", self.on_note_select)

        # أزرار الملاحظات
        tk.Button(self.left_frame, text="إضافة ملاحظة", command=self.add_note, bg="#444", fg="white").pack(pady=5)
        tk.Button(self.left_frame, text="حذف ملاحظة", command=self.delete_note, bg="#444", fg="white").pack(pady=5)

        # بحث
        self.search_entry = tk.Entry(self.left_frame, bg="white", fg="black")
        self.search_entry.pack(pady=5, padx=10, fill="x")
        tk.Button(self.left_frame, text="بحث", command=self.search_notes, bg="#444", fg="white").pack(pady=5)

        # محرر النص
        self.text_area = tk.Text(self.right_frame, wrap="word", font=("Arial", 14), bg="#1e1e1e", fg="white", insertbackground="white")
        self.text_area.pack(fill="both", expand=True, padx=10, pady=10)

        # أزرار أسفل الشاشة
        tk.Button(self.bottom_frame, text="حفظ (Ctrl+S)", command=self.save_note, bg="#444", fg="white").pack(side="right", padx=10, pady=5)
        tk.Button(self.bottom_frame, text="تصدير PDF", command=self.export_pdf, bg="#444", fg="white").pack(side="right", padx=10)
        tk.Button(self.bottom_frame, text="طباعة", command=self.print_note, bg="#444", fg="white").pack(side="right", padx=10)

    def bind_shortcuts(self):
        self.root.bind('<Control-s>', lambda e: self.save_note())
        self.root.bind('<Control-f>', lambda e: self.search_notes())

    def load_sections(self):
        if not self.verify_password():
            return
        self.sections = [d for d in os.listdir(NOTES_DIR) if os.path.isdir(os.path.join(NOTES_DIR, d))]
        self.section_listbox.delete(0, tk.END)
        for sec in self.sections:
            self.section_listbox.insert(tk.END, sec)

    def on_section_select(self, event):
        if not self.verify_password(): return
        sel = self.section_listbox.curselection()
        if sel:
            self.current_section = self.section_listbox.get(sel)
            self.load_notes()

    def load_notes(self):
        if not self.verify_password(): return
        folder = os.path.join(NOTES_DIR, self.current_section)
        self.note_listbox.delete(0, tk.END)
        for file in os.listdir(folder):
            if file.endswith('.txt'):
                self.note_listbox.insert(tk.END, file)

    def on_note_select(self, event):
        if not self.verify_password(): return
        sel = self.note_listbox.curselection()
        if sel:
            name = self.note_listbox.get(sel)
            self.current_note_path = os.path.join(NOTES_DIR, self.current_section, name)
            with open(self.current_note_path, 'r', encoding='utf-8') as f:
                text = f.read()
            self.text_area.delete('1.0', tk.END)
            self.text_area.insert(tk.END, text)

    def add_section(self):
        name = simpledialog.askstring('اسم القسم', 'أدخل اسم القسم:')
        if name:
            path = os.path.join(NOTES_DIR, name)
            os.makedirs(path, exist_ok=True)
            self.load_sections()

    def delete_section(self):
        if self.current_section:
            if messagebox.askyesno('تأكيد', f'حذف القسم {self.current_section}?'):
                shutil.rmtree(os.path.join(NOTES_DIR, self.current_section))
                self.current_section = None
                self.load_sections()
                self.note_listbox.delete(0, tk.END)
                self.text_area.delete('1.0', tk.END)

    def add_note(self):
        if not self.current_section:
            messagebox.showwarning('مطلوب', 'اختر قسمًا أولاً')
            return
        name = simpledialog.askstring('اسم الملاحظة', 'أدخل اسم الملاحظة:')
        if name:
            note_file = os.path.join(NOTES_DIR, self.current_section, f'{name}.txt')
            with open(note_file, 'w', encoding='utf-8') as f:
                f.write('')
            self.load_notes()

    def delete_note(self):
        if self.current_note_path:
            if messagebox.askyesno('تأكيد', 'هل تريد حذف الملاحظة؟'):
                os.remove(self.current_note_path)
                self.current_note_path = None
                self.load_notes()
                self.text_area.delete('1.0', tk.END)

    def save_note(self):
        if self.current_note_path:
            with open(self.current_note_path, 'w', encoding='utf-8') as f:
                f.write(self.text_area.get('1.0', tk.END).strip())
            messagebox.showinfo('تم الحفظ', 'تم حفظ الملاحظة')

    def export_pdf(self):
        if not self.current_note_path: return
        content = self.text_area.get('1.0', tk.END).strip()
        pdf = ArabicPDF()
        pdf.add_page()
        pdf.multi_cell(0, 10, content)
        dest = filedialog.asksaveasfilename(defaultextension='.pdf', filetypes=[('PDF','*.pdf')])
        if dest:
            pdf.output(dest)
            messagebox.showinfo('تم التصدير', 'تم حفظ PDF')

    def print_note(self):
        if not self.current_note_path: return
        temp = tempfile.NamedTemporaryFile(delete=False, suffix='.txt', mode='w', encoding='utf-8')
        temp.write(self.text_area.get('1.0', tk.END))
        temp.close()
        try:
            if platform.system() == 'Windows':
                os.startfile(temp.name, 'print')
            else:
                subprocess.run(['lp', temp.name])
        except Exception as e:
            messagebox.showerror('خطأ', f'فشل الطباعة: {e}')

    def search_notes(self):
        query = self.search_entry.get().strip()
        if not query: return
        results = []
        for sec in os.listdir(NOTES_DIR):
            sec_path = os.path.join(NOTES_DIR, sec)
            for note in os.listdir(sec_path):
                path = os.path.join(sec_path, note)
                with open(path, 'r', encoding='utf-8') as f:
                    if query in f.read():
                        results.append(f'{sec}/{note}')
        if results:
            win = tk.Toplevel(self.root)
            win.title('نتائج البحث')
            tk.Label(win, text=f'وجد {len(results)} نتيجة:').pack()
            lb = tk.Listbox(win, width=50)
            lb.pack()
            for item in results: lb.insert(tk.END, item)
            def open_sel():
                sel = lb.curselection()
                if sel:
                    sec, note = lb.get(sel).split('/')
                    self.section_listbox.selection_clear(0, tk.END)
                    for i in range(self.section_listbox.size()):
                        if self.section_listbox.get(i)==sec:
                            self.section_listbox.selection_set(i)
                            self.on_section_select(None)
                            self.select_note_by_name(note)
                            break
                    win.destroy()
            tk.Button(win, text='فتح', command=open_sel).pack(pady=5)
        else:
            messagebox.showinfo('نتائج البحث','لا توجد نتائج')

    def select_note_by_name(self, note_name):
        for i in range(self.note_listbox.size()):
            if self.note_listbox.get(i)==note_name:
                self.note_listbox.selection_set(i)
                self.on_note_select(None)
                break

    def auto_backup(self):
        now = time.strftime('%Y%m%d_%H%M%S')
        backup_dir = os.path.join(NOTES_DIR, f'backup_{now}')
        try:
            shutil.copytree(NOTES_DIR, backup_dir)
        except Exception:
            pass

    def schedule_auto_backup(self, minutes=60):
        def loop():
            while True:
                self.auto_backup()
                time.sleep(minutes*60)
        t = threading.Thread(target=loop, daemon=True)
        t.start()

    def set_password(self):
        pwd = simpledialog.askstring('كلمة المرور','أدخل كلمة المرور:', show='*')
        if pwd:
            self.password_set = True
            self.password = pwd
            with open(os.path.join(NOTES_DIR, 'password.txt'),'w') as f:
                f.write(pwd)
            messagebox.showinfo('تم','تم تعيين كلمة المرور')

    def verify_password(self):
        pwd_file = os.path.join(NOTES_DIR,'password.txt')
        if os.path.exists(pwd_file):
            stored = open(pwd_file).read().strip()
            attempt = simpledialog.askstring('تحقق','أدخل كلمة المرور:', show='*')
            if attempt!=stored:
                messagebox.showerror('خطأ','كلمة المرور خاطئة')
                return False
        return True

if __name__ == '__main__':
    root = tk.Tk()
    app = NotedxApp(root)
    app.schedule_auto_backup(60)
    root.mainloop()