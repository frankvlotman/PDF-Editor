import os
import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import ttk
from pypdf import PdfReader, PdfWriter
from reportlab.lib.pagesizes import letter, landscape
from reportlab.pdfgen import canvas
from reportlab.lib.colors import red, black, blue
from PyPDF2 import PdfReader as PyPDF2Reader, PdfWriter as PyPDF2Writer
import tempfile

class PDFApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("PDF Tools")
        self.geometry("900x600")

        self.notebook = ttk.Notebook(self)
        self.notebook.pack(expand=True, fill='both')

        self.pdf_editor_tab = PDFEditorTab(self.notebook)
        self.portrait_tab = PortraitModeTab(self.notebook)
        self.landscape_tab = LandscapeModeTab(self.notebook)

        self.notebook.add(self.pdf_editor_tab, text='PDF Editor')
        self.notebook.add(self.portrait_tab, text='Portrait Mode')
        self.notebook.add(self.landscape_tab, text='Landscape Mode')

class PDFEditorTab(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.reader = None
        self.additional_pages = []
        self.pages_to_keep = []

        # Create widgets
        ttk.Button(self, text="Open PDF", command=self.open_pdf).pack(pady=5)
        self.pages_list = tk.Listbox(self, selectmode=tk.MULTIPLE)
        self.pages_list.pack(fill=tk.BOTH, expand=True, pady=5)
        ttk.Button(self, text="Add Pages from Other PDFs", command=self.add_pages).pack(pady=5)
        ttk.Button(self, text="Delete Selected Pages", command=self.delete_pages).pack(pady=5)
        ttk.Button(self, text="Save PDF", command=self.save_pdf).pack(pady=5)

    def open_pdf(self):
        file_path = filedialog.askopenfilename(title="Select PDF file", filetypes=[("PDF Files", "*.pdf")])
        if file_path:
            self.reader = PdfReader(file_path)
            self.pages_to_keep = list(range(len(self.reader.pages)))
            self.load_pages()

    def load_pages(self):
        try:
            if self.reader is None:
                raise Exception("No PDF file is loaded.")
            
            self.pages_list.delete(0, tk.END)
            for i in range(len(self.reader.pages)):
                self.pages_list.insert(tk.END, f"Original Page {i+1}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load PDF: {e}")

    def delete_pages(self):
        selected_pages = self.pages_list.curselection()
        if not selected_pages:
            messagebox.showinfo("Info", "Please select one or more pages to delete.")
            return

        for page_idx in selected_pages:
            self.pages_list.delete(page_idx)
            self.pages_list.insert(page_idx, f"Original Page {page_idx + 1} - Deleted")

        self.pages_to_keep = [i for i in self.pages_to_keep if i not in selected_pages]
        messagebox.showinfo("Success", "Pages marked for deletion. Save the document to apply changes.")

    def add_pages(self):
        new_pdfs = filedialog.askopenfilenames(title="Select PDFs to add", filetypes=[("PDF Files", "*.pdf")])
        if new_pdfs:
            try:
                self.additional_pages.clear()
                self.pages_list.insert(tk.END, "Added Pages:")
                for pdf_path in new_pdfs:
                    new_reader = PdfReader(pdf_path)
                    self.additional_pages.extend(new_reader.pages)
                    for i in range(len(new_reader.pages)):
                        self.pages_list.insert(tk.END, f"Added Page {i+1} from {os.path.basename(pdf_path)}")

                messagebox.showinfo("Success", f"Pages from {len(new_pdfs)} PDF(s) will be added before saving.")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load additional PDFs: {e}")

    def save_pdf(self):
        try:
            if self.reader is None:
                raise Exception("No PDF file is loaded.")
            
            writer = PdfWriter()

            for i in self.pages_to_keep:
                writer.add_page(self.reader.pages[i])

            if self.additional_pages:
                for page in self.additional_pages:
                    writer.add_page(page)

            output_filename = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("PDF Files", "*.pdf")])
            
            if output_filename:
                with open(output_filename, "wb") as output_file:
                    writer.write(output_file)

                messagebox.showinfo("Success", f"File saved as '{output_filename}' with the selected changes applied.")
                self.pages_list.delete(0, tk.END)

        except Exception as e:
            messagebox.showerror("Error", f"Failed to save the file: {e}")

class PortraitModeTab(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        self.scale_factor = 0.4
        self.canvas_width = int(612 * self.scale_factor)
        self.canvas_height = int(792 * self.scale_factor)
        
        main_frame = ttk.Frame(self)
        main_frame.pack(expand=True, fill='both')

        self.canvas = tk.Canvas(main_frame, width=self.canvas_width, height=self.canvas_height, bg='white')
        self.canvas.pack(side='left', padx=10, pady=10)

        controls_frame = ttk.Frame(main_frame)
        controls_frame.pack(side='left', fill='y', padx=10, pady=10)

        self.text_id = self.canvas.create_text(
            self.canvas_width // 2, 0, text="Sample Text", anchor='n',
            font=("Helvetica-Bold", int(20 * self.scale_factor)), fill="red"
        )

        self.canvas.tag_bind(self.text_id, "<Button1-Motion>", self.drag_text)

        ttk.Label(controls_frame, text="Enter text for the stamp:").pack(pady=2)
        self.text_entry = ttk.Entry(controls_frame, width=30)
        self.text_entry.pack(pady=2)
        self.text_entry.bind('<KeyRelease>', self.update_canvas_text)

        ttk.Label(controls_frame, text="Enter font size:").pack(pady=2)
        self.font_size_entry = ttk.Entry(controls_frame, width=10)
        self.font_size_entry.pack(pady=2)
        self.font_size_entry.bind('<KeyRelease>', self.update_canvas_text)
        self.font_size_entry.insert(0, "20")

        ttk.Label(controls_frame, text="Select font color:").pack(pady=2)
        self.font_color = tk.StringVar()
        self.font_color.set('red')
        color_options = ['black', 'blue', 'red']
        self.color_menu = ttk.OptionMenu(controls_frame, self.font_color, *color_options, command=self.update_canvas_text)
        self.color_menu.pack(pady=2)

        self.underline = tk.BooleanVar()
        ttk.Checkbutton(controls_frame, text="Underline", variable=self.underline, command=self.update_canvas_text).pack(pady=2)

        ttk.Button(controls_frame, text="Update Position", command=self.update_position).pack(pady=2)
        ttk.Button(controls_frame, text="45 Degrees", command=lambda: self.process_text_overlay(angle=45)).pack(pady=2)
        ttk.Button(controls_frame, text="Horizontal", command=self.process_text_overlay).pack(pady=2)

        self.final_x_pos = None
        self.final_y_pos = None

    def drag_text(self, event):
        new_x, new_y = event.x, event.y
        new_x = max(0, min(new_x, self.canvas_width))
        new_y = max(0, min(new_y, self.canvas_height))
        self.canvas.coords(self.text_id, new_x, new_y)

    def update_canvas_text(self, event=None):
        new_text = self.text_entry.get()
        new_font_size = self.font_size_entry.get()
        selected_color = self.font_color.get()
        underline = self.underline.get()

        try:
            font_size = int(new_font_size)
        except ValueError:
            font_size = 20

        scaled_font_size = max(int(font_size * self.scale_factor), 1)
        font_style = ("Helvetica-Bold", scaled_font_size)
        if underline:
            font_style += ('underline',)

        self.canvas.itemconfig(self.text_id, text=new_text, font=font_style, fill=selected_color)

    def update_position(self):
        coords = self.canvas.coords(self.text_id)
        self.final_x_pos, self.final_y_pos = coords
        messagebox.showinfo("Position Updated", f"Position set to: ({self.final_x_pos}, {self.final_y_pos})")

    def get_text_position(self):
        if self.final_x_pos is None or self.final_y_pos is None:
            coords = self.canvas.coords(self.text_id)
            self.final_x_pos, self.final_y_pos = coords

        inverted_y_pos = self.canvas_height - self.final_y_pos
        return int(self.final_x_pos / self.scale_factor), int(inverted_y_pos / self.scale_factor)

    def process_text_overlay(self, angle=None):
        text = self.text_entry.get()
        font_size = self.font_size_entry.get()
        selected_color = self.font_color.get()
        underline = self.underline.get()

        if not text:
            messagebox.showerror("Input Error", "Please enter the text for the stamp.")
            return

        try:
            font_size = int(font_size)
        except ValueError:
            messagebox.showerror("Input Error", "Please enter a valid font size.")
            return

        x_pos, y_pos = self.get_text_position()

        base_pdf_path = filedialog.askopenfilename(filetypes=[("PDF files", "*.pdf")])
        if not base_pdf_path:
            return

        output_pdf_path = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("PDF files", "*.pdf")])
        if not output_pdf_path:
            return

        self.add_text_to_existing_pdf(
            base_pdf_path, text, output_pdf_path, font_size, x_pos, y_pos,
            angle=angle, orientation='portrait', color=selected_color, underline=underline
        )

        messagebox.showinfo("Success", "PDF with text stamp saved successfully!")

    def add_text_to_existing_pdf(self, base_pdf_path, text, output_pdf_path, font_size, x_pos, y_pos, angle=None, orientation='portrait', color='red', underline=False):
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_pdf:
            temp_pdf_path = temp_pdf.name
            self.create_text_overlay(temp_pdf_path, text, font_size, x_pos, y_pos, angle=angle, orientation=orientation, color=color, underline=underline)

        reader_base = PyPDF2Reader(base_pdf_path)
        reader_stamp = PyPDF2Reader(temp_pdf_path)
        writer = PyPDF2Writer()

        stamp_page = reader_stamp.pages[0]

        for base_page in reader_base.pages:
            base_page.merge_page(stamp_page)
            writer.add_page(base_page)

        with open(output_pdf_path, 'wb') as f:
            writer.write(f)

        os.remove(temp_pdf_path)

    def create_text_overlay(self, temp_pdf_path, text, font_size, x_pos, y_pos, angle=None, orientation='portrait', color='red', underline=False):
        page_size = letter if orientation == 'portrait' else landscape(letter)
        page_width, page_height = page_size

        c = canvas.Canvas(temp_pdf_path, pagesize=page_size)
        c.setFont("Helvetica-Bold", font_size)

        color_dict = {'red': red, 'blue': blue, 'black': black}
        text_color = color_dict.get(color, red)

        c.setFillColor(text_color)
        c.setStrokeColor(text_color)

        adjusted_y_pos = y_pos
        ascent = font_size * 0.8

        if adjusted_y_pos + ascent > page_height:
            adjusted_y_pos = page_height - ascent
        elif adjusted_y_pos - font_size * 0.2 < 0:
            adjusted_y_pos = font_size * 0.2

        if angle is not None:
            c.saveState()
            c.translate(x_pos, adjusted_y_pos)
            c.rotate(angle)
            c.drawCentredString(0, 0, text)
            text_width = c.stringWidth(text, "Helvetica-Bold", font_size)
            if underline:
                c.setLineWidth(1)
                c.line(-text_width / 2, -2, text_width / 2, -2)
            c.restoreState()
        else:
            c.drawCentredString(x_pos, adjusted_y_pos, text)
            text_width = c.stringWidth(text, "Helvetica-Bold", font_size)
            if underline:
                c.setLineWidth(1)
                c.line(x_pos - text_width / 2, adjusted_y_pos - 2, x_pos + text_width / 2, adjusted_y_pos - 2)

        c.save()

class LandscapeModeTab(PortraitModeTab):
  def __init__(self, parent):
      super().__init__(parent)

  def init_ui(self):
      self.scale_factor = 0.4
      self.canvas_width = int(792 * self.scale_factor)
      self.canvas_height = int(612 * self.scale_factor)
      
      main_frame = ttk.Frame(self)
      main_frame.pack(expand=True, fill='both')

      self.canvas = tk.Canvas(main_frame, width=self.canvas_width, height=self.canvas_height, bg='white')
      self.canvas.pack(side='left', padx=10, pady=10)

      controls_frame = ttk.Frame(main_frame)
      controls_frame.pack(side='left', fill='y', padx=10, pady=10)

      self.text_id = self.canvas.create_text(
          self.canvas_width // 2, self.canvas_height // 2, text="Sample Text",
          font=("Helvetica-Bold", int(20 * self.scale_factor)), fill="red"
      )

      self.canvas.tag_bind(self.text_id, "<Button1-Motion>", self.drag_text)

      ttk.Label(controls_frame, text="Enter text for the stamp:").pack(pady=2)
      self.text_entry = ttk.Entry(controls_frame, width=30)
      self.text_entry.pack(pady=2)
      self.text_entry.bind('<KeyRelease>', self.update_canvas_text)

      ttk.Label(controls_frame, text="Enter font size:").pack(pady=2)
      self.font_size_entry = ttk.Entry(controls_frame, width=10)
      self.font_size_entry.pack(pady=2)
      self.font_size_entry.bind('<KeyRelease>', self.update_canvas_text)
      self.font_size_entry.insert(0, "20")

      ttk.Label(controls_frame, text="Select font color:").pack(pady=2)
      self.font_color = tk.StringVar()
      self.font_color.set('red')
      color_options = ['black', 'blue', 'red']
      self.color_menu = ttk.OptionMenu(controls_frame, self.font_color, *color_options, command=self.update_canvas_text)
      self.color_menu.pack(pady=2)

      self.underline = tk.BooleanVar()
      ttk.Checkbutton(controls_frame, text="Underline", variable=self.underline, command=self.update_canvas_text).pack(pady=2)

      ttk.Button(controls_frame, text="Update Position", command=self.update_position).pack(pady=2)
      ttk.Button(controls_frame, text="45 Degrees", command=lambda: self.process_text_overlay(angle=45)).pack(pady=2)
      ttk.Button(controls_frame, text="Horizontal", command=self.process_text_overlay).pack(pady=2)

      self.final_x_pos = None
      self.final_y_pos = None

  def process_text_overlay(self, angle=None):
      text = self.text_entry.get()
      font_size = self.font_size_entry.get()
      selected_color = self.font_color.get()
      underline = self.underline.get()

      if not text:
          messagebox.showerror("Input Error", "Please enter the text for the stamp.")
          return

      try:
          font_size = int(font_size)
      except ValueError:
          messagebox.showerror("Input Error", "Please enter a valid font size.")
          return

      x_pos, y_pos = self.get_text_position()

      base_pdf_path = filedialog.askopenfilename(filetypes=[("PDF files", "*.pdf")])
      if not base_pdf_path:
          return

      output_pdf_path = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("PDF files", "*.pdf")])
      if not output_pdf_path:
          return

      self.add_text_to_existing_pdf(
          base_pdf_path, text, output_pdf_path, font_size, x_pos, y_pos,
          angle=angle, orientation='landscape', color=selected_color, underline=underline
      )

      messagebox.showinfo("Success", "PDF with text stamp saved successfully!")

# Main application
if __name__ == "__main__":
  app = PDFApp()
  app.mainloop()

