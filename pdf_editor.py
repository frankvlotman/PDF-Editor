import os
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog
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
        self.geometry("1000x700")  # Increased width for better layout with new buttons

        # Initialize ttk style
        style = ttk.Style()
        
        # Use 'clam' theme for better customization
        style.theme_use('clam')

        # Define a new style for light blue buttons
        style.configure('LightBlue.TButton',
                        background='#d0e8f1',  # Light blue background
                        foreground='black',    # Default text color
                        borderwidth=1,
                        focusthickness=3,
                        focuscolor='none')

        # Define the hover (active) background color
        style.map('LightBlue.TButton',
                  background=[('active', '#87CEFA')],  # Slightly darker light blue on hover
                  foreground=[('active', 'black')])

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
        self.pages_to_keep = []  # List of original page indices to keep
        self.additional_pages = []  # List of added pages from other PDFs
        self.current_pages = []  # Unified list to manage ordering
        self.style = ttk.Style()
        self.style.configure("Treeview", rowheight=25)

        # Create widgets with the new LightBlue.TButton style
        button_frame = ttk.Frame(self)
        button_frame.pack(pady=5)

        ttk.Button(button_frame, text="Open PDF", style='LightBlue.TButton', command=self.open_pdf).grid(row=0, column=0, padx=5, pady=5)
        ttk.Button(button_frame, text="Merge PDFs", style='LightBlue.TButton', command=self.merge_pdfs).grid(row=0, column=1, padx=5, pady=5)
        ttk.Button(button_frame, text="Split PDF", style='LightBlue.TButton', command=self.split_pdf).grid(row=0, column=2, padx=5, pady=5)

        # Instructional Label
        instruction_label = ttk.Label(self, text="Click on a page to drag and drop to edit the order of pages.", font=("Helvetica", 10, "italic"))
        instruction_label.pack(pady=(10, 0))  # Add some padding above the label

        # Create a frame to hold the Listbox and Scrollbar
        self.pages_frame = ttk.Frame(self)
        self.pages_frame.pack(fill=tk.BOTH, expand=True, pady=5, padx=10)

        # Create the Listbox
        self.pages_list = tk.Listbox(self.pages_frame, selectmode=tk.MULTIPLE)
        self.pages_list.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Enable drag-and-drop
        self.pages_list.bind('<Button-1>', self.on_click)
        self.pages_list.bind('<B1-Motion>', self.on_drag)
        self.drag_data = {"item": None}

        # Create the Scrollbar
        self.scrollbar = ttk.Scrollbar(self.pages_frame, orient=tk.VERTICAL, command=self.pages_list.yview)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Configure the Listbox to use the Scrollbar
        self.pages_list.config(yscrollcommand=self.scrollbar.set)

        # Buttons for page operations
        operation_frame = ttk.Frame(self)
        operation_frame.pack(pady=5)

        ttk.Button(operation_frame, text="Add Pages from Other PDFs", style='LightBlue.TButton', command=self.add_pages).grid(row=0, column=0, padx=5, pady=5)
        ttk.Button(operation_frame, text="Delete Selected Pages", style='LightBlue.TButton', command=self.delete_pages).grid(row=0, column=1, padx=5, pady=5)
        ttk.Button(operation_frame, text="Extract Selected Pages", style='LightBlue.TButton', command=self.extract_pages).grid(row=0, column=2, padx=5, pady=5)
        ttk.Button(operation_frame, text="Save PDF", style='LightBlue.TButton', command=self.save_pdf).grid(row=0, column=3, padx=5, pady=5)

    def open_pdf(self):
        file_path = filedialog.askopenfilename(title="Select PDF file", filetypes=[("PDF Files", "*.pdf")])
        if file_path:
            self.reader = PdfReader(file_path)
            self.pages_to_keep = list(range(len(self.reader.pages)))
            self.additional_pages = []
            self.current_pages = [{'type': 'original', 'page_num': i, 'page': self.reader.pages[i]} for i in self.pages_to_keep]
            self.load_pages()

    def load_pages(self):
        try:
            if self.reader is None:
                raise Exception("No PDF file is loaded.")
            
            self.pages_list.delete(0, tk.END)
            for page in self.current_pages:
                if page['type'] == 'original':
                    self.pages_list.insert(tk.END, f"Original Page {page['page_num'] +1}")
                elif page['type'] == 'added':
                    self.pages_list.insert(tk.END, f"Added Page from {page['source']} - Page {page['page_num']}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load PDF: {e}")

    def delete_pages(self):
        selected_pages = self.pages_list.curselection()
        if not selected_pages:
            messagebox.showinfo("Info", "Please select one or more pages to delete.")
            return

        # Identify original pages to delete before modifying the listbox
        original_selected = [
            idx for idx in selected_pages
            if self.current_pages[idx]['type'] == 'original'
        ]

        if not original_selected:
            messagebox.showinfo("Info", "Please select one or more original pages to delete.")
            return

        # Remove selected original pages from pages_to_keep and current_pages
        pages_to_remove = sorted(original_selected, reverse=True)
        for idx in pages_to_remove:
            # Mark as deleted in the Listbox
            entry = self.pages_list.get(idx)
            self.pages_list.delete(idx)
            self.pages_list.insert(idx, f"{entry} - Deleted")
            # Remove from current_pages
            self.current_pages.pop(idx)
            self.pages_to_keep.pop(idx)

        messagebox.showinfo("Success", "Pages marked for deletion. Save the document to apply changes.")

    def add_pages(self):
        new_pdfs = filedialog.askopenfilenames(title="Select PDFs to add", filetypes=[("PDF Files", "*.pdf")])
        if new_pdfs:
            try:
                for pdf_path in new_pdfs:
                    new_reader = PdfReader(pdf_path)
                    for i in range(len(new_reader.pages)):
                        page_info = {
                            'type': 'added',
                            'source': os.path.basename(pdf_path),
                            'page_num': i + 1,
                            'page': new_reader.pages[i]
                        }
                        self.additional_pages.append(page_info)
                        self.current_pages.append(page_info)
                        self.pages_list.insert(tk.END, f"Added Page from {os.path.basename(pdf_path)} - Page {i+1}")
                messagebox.showinfo("Success", f"Pages from {len(new_pdfs)} PDF(s) added successfully.")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load additional PDFs: {e}")

    def extract_pages(self):
        selected_indices = self.pages_list.curselection()
        if not selected_indices:
            messagebox.showinfo("Info", "Please select one or more pages to extract.")
            return

        pages_to_extract = []
        for idx in selected_indices:
            page = self.current_pages[idx]['page']
            pages_to_extract.append(page)

        if not pages_to_extract:
            messagebox.showinfo("Info", "No valid pages selected to extract.")
            return

        writer = PdfWriter()
        for page in pages_to_extract:
            writer.add_page(page)

        output_filename = filedialog.asksaveasfilename(defaultextension=".pdf",
                                                       filetypes=[("PDF Files", "*.pdf")],
                                                       title="Save Extracted Pages As")
        if output_filename:
            try:
                with open(output_filename, "wb") as output_file:
                    writer.write(output_file)
                messagebox.showinfo("Success", f"Extracted pages saved as '{output_filename}'.")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save the extracted pages: {e}")

    def save_pdf(self):
        try:
            if self.reader is None:
                raise Exception("No PDF file is loaded.")
            
            writer = PdfWriter()

            # Add pages in the order of current_pages
            for page_info in self.current_pages:
                writer.add_page(page_info['page'])

            output_filename = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("PDF Files", "*.pdf")],
                                                           title="Save PDF As")
            
            if output_filename:
                with open(output_filename, "wb") as output_file:
                    writer.write(output_file)

                messagebox.showinfo("Success", f"File saved as '{output_filename}' with the selected changes applied.")
                self.load_pages()  # Reload pages to reflect any deletions
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save the file: {e}")

    def merge_pdfs(self):
        pdf_files = filedialog.askopenfilenames(title="Select PDFs to Merge", filetypes=[("PDF Files", "*.pdf")])
        if pdf_files:
            try:
                merger = PdfWriter()
                for pdf in pdf_files:
                    reader = PdfReader(pdf)
                    for page in reader.pages:
                        merger.add_page(page)
                output_filename = filedialog.asksaveasfilename(defaultextension=".pdf",
                                                               filetypes=[("PDF Files", "*.pdf")],
                                                               title="Save Merged PDF As")
                if output_filename:
                    with open(output_filename, "wb") as f:
                        merger.write(f)
                    messagebox.showinfo("Success", f"Merged PDF saved as '{output_filename}'.")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to merge PDFs: {e}")

    def split_pdf(self):
        if self.reader is None:
            messagebox.showerror("Error", "No PDF file is loaded.")
            return

        page_ranges_str = simpledialog.askstring("Split PDF", "Enter page ranges to split (e.g., 1-3,5,7-9):")
        if not page_ranges_str:
            return

        try:
            ranges = self.parse_page_ranges(page_ranges_str)
            for idx, (start, end) in enumerate(ranges, 1):
                writer = PdfWriter()
                for page_num in range(start-1, end):
                    if page_num < len(self.reader.pages):
                        writer.add_page(self.reader.pages[page_num])
                    else:
                        raise Exception(f"Page number {page_num +1} exceeds the total number of pages.")
                output_filename = filedialog.asksaveasfilename(defaultextension=".pdf",
                                                               filetypes=[("PDF Files", "*.pdf")],
                                                               title=f"Save Split PDF {idx} As")
                if output_filename:
                    with open(output_filename, "wb") as f:
                        writer.write(f)
            messagebox.showinfo("Success", "PDF split successfully.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to split PDF: {e}")

    def parse_page_ranges(self, ranges_str):
        ranges = []
        parts = ranges_str.split(',')
        for part in parts:
            if '-' in part:
                start, end = part.split('-')
                start, end = int(start.strip()), int(end.strip())
                if start > end:
                    raise ValueError(f"Invalid range: {part}")
                ranges.append((start, end))
            else:
                num = int(part.strip())
                ranges.append((num, num))
        return ranges

    def on_click(self, event):
        # Record the index of the clicked item
        self.drag_data["item"] = self.pages_list.nearest(event.y)

    def on_drag(self, event):
        # Get the index of the item where the mouse is dragged to
        new_index = self.pages_list.nearest(event.y)
        if new_index != self.drag_data["item"]:
            # Get the text of the item to move
            item_text = self.pages_list.get(self.drag_data["item"])
            # Remove the item from its original position
            self.pages_list.delete(self.drag_data["item"])
            # Insert the item at the new position
            self.pages_list.insert(new_index, item_text)
            # Update drag_data to the new position
            self.drag_data["item"] = new_index

            # Reorder current_pages based on the new Listbox order
            self.reorder_current_pages()

    def reorder_current_pages(self):
        # Reconstruct current_pages based on the current Listbox order
        new_current_pages = []
        for idx in range(self.pages_list.size()):
            entry = self.pages_list.get(idx)
            if entry.startswith("Original Page") and "Deleted" not in entry:
                page_num = int(entry.split(" ")[2]) - 1
                new_current_pages.append({'type': 'original', 'page_num': page_num, 'page': self.reader.pages[page_num]})
            elif entry.startswith("Added Page"):
                # Extract source and page_num
                try:
                    parts = entry.split(" ")
                    source = parts[3]
                    page_num = int(parts[5])
                    # Find the corresponding added page
                    for added_page in self.additional_pages:
                        if added_page['source'] == source and added_page['page_num'] == page_num:
                            new_current_pages.append(added_page)
                            break
                except (IndexError, ValueError):
                    continue
            elif "Deleted" in entry:
                # Skip deleted pages
                continue
        self.current_pages = new_current_pages

    # Optional: Implement drag-and-drop for rearranging additional pages as well
    # This is handled in reorder_current_pages()


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

        # Apply the LightBlue.TButton style to these buttons
        ttk.Button(controls_frame, text="Update Position", style='LightBlue.TButton', command=self.update_position).pack(pady=2)
        ttk.Button(controls_frame, text="45 Degrees", style='LightBlue.TButton', command=lambda: self.process_text_overlay(angle=45)).pack(pady=2)
        ttk.Button(controls_frame, text="Horizontal", style='LightBlue.TButton', command=self.process_text_overlay).pack(pady=2)

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

        # Apply the LightBlue.TButton style to these buttons
        ttk.Button(controls_frame, text="Update Position", style='LightBlue.TButton', command=self.update_position).pack(pady=2)
        ttk.Button(controls_frame, text="45 Degrees", style='LightBlue.TButton', command=lambda: self.process_text_overlay(angle=45)).pack(pady=2)
        ttk.Button(controls_frame, text="Horizontal", style='LightBlue.TButton', command=self.process_text_overlay).pack(pady=2)

        self.final_x_pos = None
        self.final_y_pos = None


# Main application
if __name__ == "__main__":
    app = PDFApp()
    app.mainloop()
