from fpdf import FPDF
import pandas as pd
from datetime import datetime

# Custom PDF class with better design and UTF-8 support
class CustomPDF(FPDF):
    def __init__(self):
        super().__init__()
        # Add support for more characters
        self.add_page()
        
    def header(self):
        # Set font
        self.set_font('Arial', 'B', 20)
        
        # Title
        self.cell(0, 10, 'DMS ANALYTICS REPORT', 0, 1, 'C')
        
        # Subtitle
        self.set_font('Arial', 'I', 12)
        self.cell(0, 10, 'Comprehensive Document Management System Analysis', 0, 1, 'C')
        
        # Line break
        self.ln(10)
    
    def footer(self):
        # Position at 1.5 cm from bottom
        self.set_y(-15)
        
        # Set font
        self.set_font('Arial', 'I', 8)
        
        # Page number
        self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')
    
    def chapter_title(self, title):
        # Set font
        self.set_font('Arial', 'B', 16)
        
        # Background color
        self.set_fill_color(200, 220, 255)
        
        # Title
        self.cell(0, 10, title, 0, 1, 'L', 1)
        
        # Line break
        self.ln(4)
    
    def safe_text(self, text):
        """Convert text to ASCII-safe characters"""
        if isinstance(text, str):
            # Replace problematic characters
            text = text.replace('•', '-')
            text = text.replace('✅', '[OK]')
            text = text.replace('❌', '[ERROR]')
            text = text.replace('📊', '[CHART]')
            text = text.replace('📄', '[DOC]')
            text = text.replace('🔄', '[REFRESH]')
            # Remove any other non-ASCII characters
            text = text.encode('ascii', 'ignore').decode('ascii')
        return str(text)
    
    def add_metric_card(self, title, value, width=45, height=20):
        # Set fill color for metric card
        self.set_fill_color(240, 240, 240)
        
        # Draw metric card with safe text
        safe_title = self.safe_text(title)
        safe_value = self.safe_text(value)
        self.cell(width, height, f"{safe_title}: {safe_value}", 1, 0, 'C', 1)
    
    def add_table_header(self, headers, col_widths):
        # Set font for header
        self.set_font('Arial', 'B', 10)
        
        # Set fill color for header
        self.set_fill_color(200, 200, 200)
        
        # Add header cells with safe text
        for i, header in enumerate(headers):
            safe_header = self.safe_text(header)
            self.cell(col_widths[i], 10, safe_header, 1, 0, 'C', 1)
        
        self.ln()
    
    def add_table_row(self, data, col_widths):
        # Set font for data
        self.set_font('Arial', '', 10)
        
        # Add data cells with safe text
        for i, cell in enumerate(data):
            safe_cell = self.safe_text(cell)
            self.cell(col_widths[i], 8, safe_cell, 1, 0, 'L')
        
        self.ln()

# Function to create PDF report with custom design
def create_pdf_report(data, filtered_docs, date_range, department_filter, doc_type_filter):
    pdf = CustomPDF()
    pdf.add_page()
    
    # Set auto page break
    pdf.set_auto_page_break(auto=True, margin=15)
    
    # Report metadata
    pdf.set_font('Arial', '', 10)
    pdf.cell(0, 8, f"Report Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", 0, 1)
    pdf.cell(0, 8, f"Date Range: {date_range[0]} to {date_range[1]}", 0, 1)
    pdf.cell(0, 8, f"Departments: {', '.join(department_filter) if department_filter else 'All Departments'}", 0, 1)
    pdf.cell(0, 8, f"Document Types: {', '.join(doc_type_filter) if doc_type_filter else 'All Types'}", 0, 1)
    pdf.ln(10)
    
    # Executive Summary
    pdf.chapter_title("EXECUTIVE SUMMARY")
    
    # Key Metrics in a grid layout
    total_docs = len(data['documents']) if 'documents' in data else 0
    total_users = len(data['users']) if 'users' in data else 0
    active_docs = len(data['documents'][data['documents']['status'] == 'active']) if 'documents' in data and 'status' in data['documents'].columns else 0
    total_announcements = len(data['announcements']) if 'announcements' in data else 0
    
    # Create metrics grid
    pdf.set_font('Arial', 'B', 12)
    pdf.add_metric_card("Total Documents", total_docs)
    pdf.add_metric_card("Total Users", total_users)
    pdf.ln(12)
    pdf.add_metric_card("Active Documents", active_docs)
    pdf.add_metric_card("Announcements", total_announcements)
    pdf.ln(15)
    
    # Document Analysis
    pdf.chapter_title("DOCUMENT ANALYSIS")
    
    if not filtered_docs.empty:
        # Documents by type
        if 'name' in filtered_docs.columns:
            pdf.set_font('Arial', 'B', 12)
            pdf.cell(0, 10, "Documents by Type:", 0, 1)
            pdf.set_font('Arial', '', 10)
            
            doc_type_counts = filtered_docs['name'].value_counts()
            for doc_type, count in doc_type_counts.items():
                safe_doc_type = pdf.safe_text(doc_type)
                pdf.cell(0, 8, f"- {safe_doc_type}: {count} documents", 0, 1)
            pdf.ln(5)
        
        # Documents by status
        if 'status' in filtered_docs.columns:
            pdf.set_font('Arial', 'B', 12)
            pdf.cell(0, 10, "Documents by Status:", 0, 1)
            pdf.set_font('Arial', '', 10)
            
            status_counts = filtered_docs['status'].value_counts()
            for status, count in status_counts.items():
                safe_status = pdf.safe_text(status)
                pdf.cell(0, 8, f"- {safe_status}: {count} documents", 0, 1)
            pdf.ln(5)
    else:
        pdf.cell(0, 8, "No document data available for selected filters", 0, 1)
    
    pdf.ln(10)
    
    # User Analysis
    pdf.chapter_title("USER ANALYSIS")
    
    if 'users' in data and not data['users'].empty:
        # Users by role
        if 'role' in data['users'].columns:
            pdf.set_font('Arial', 'B', 12)
            pdf.cell(0, 10, "Users by Role:", 0, 1)
            pdf.set_font('Arial', '', 10)
            
            role_counts = data['users']['role'].value_counts()
            for role, count in role_counts.items():
                safe_role = pdf.safe_text(role)
                pdf.cell(0, 8, f"- {safe_role}: {count} users", 0, 1)
            pdf.ln(5)
        
        # Users by status
        if 'status' in data['users'].columns:
            pdf.set_font('Arial', 'B', 12)
            pdf.cell(0, 10, "Users by Status:", 0, 1)
            pdf.set_font('Arial', '', 10)
            
            status_counts = data['users']['status'].value_counts()
            for status, count in status_counts.items():
                safe_status = pdf.safe_text(status)
                pdf.cell(0, 8, f"- {safe_status}: {count} users", 0, 1)
            pdf.ln(5)
    else:
        pdf.cell(0, 8, "No user data available", 0, 1)
    
    pdf.ln(10)
    
    # Recent Activity
    pdf.chapter_title("RECENT ACTIVITY")
    
    if not filtered_docs.empty and 'created_at' in filtered_docs.columns:
        pdf.set_font('Arial', 'B', 12)
        pdf.cell(0, 10, "Recent Documents:", 0, 1)
        pdf.set_font('Arial', '', 10)
        
        # Get recent documents
        recent_docs = filtered_docs.nlargest(5, 'created_at')
        
        for _, row in recent_docs.iterrows():
            title = row.get('title', 'N/A')
            doc_type = row.get('name', 'N/A')
            status = row.get('status', 'N/A')
            created_at = row.get('created_at', 'N/A')
            
            if isinstance(created_at, pd.Timestamp):
                created_at = created_at.strftime('%Y-%m-%d %H:%M')
            
            # Use safe text for all values
            safe_title = pdf.safe_text(title)[:50] + "..." if len(str(title)) > 50 else pdf.safe_text(title)
            safe_doc_type = pdf.safe_text(doc_type)
            safe_status = pdf.safe_text(status)
            
            pdf.cell(0, 8, f"- {safe_title}", 0, 1)
            pdf.cell(0, 8, f"  Type: {safe_doc_type} | Status: {safe_status} | Created: {created_at}", 0, 1)
            pdf.ln(2)
    else:
        pdf.cell(0, 8, "No recent activity data available", 0, 1)
    
    pdf.ln(10)
    
    # Detailed Tables (optional - add more pages if needed)
    if not filtered_docs.empty and len(filtered_docs) <= 20:  # Only show table if not too many rows
        pdf.add_page()
        pdf.chapter_title("DETAILED DOCUMENT LIST")
        
        # Table headers
        headers = ['ID', 'Title', 'Type', 'Status', 'Created']
        col_widths = [15, 70, 40, 30, 35]
        
        pdf.add_table_header(headers, col_widths)
        
        # Table rows
        for _, row in filtered_docs.iterrows():
            doc_id = row.get('doc_id', 'N/A')
            title = str(row.get('title', 'N/A'))
            doc_type = row.get('name', 'N/A')
            status = row.get('status', 'N/A')
            created_at = row.get('created_at', 'N/A')
            
            if isinstance(created_at, pd.Timestamp):
                created_at = created_at.strftime('%Y-%m-%d')
            
            # Use safe text for all values
            safe_title = pdf.safe_text(title)[:40] + "..." if len(str(title)) > 40 else pdf.safe_text(title)
            safe_doc_type = pdf.safe_text(doc_type)
            safe_status = pdf.safe_text(status)
            
            pdf.add_table_row([doc_id, safe_title, safe_doc_type, safe_status, created_at], col_widths)
    
    return pdf

# Function to create download link for PDF
def create_download_link(pdf_output, filename):
    import base64
    b64 = base64.b64encode(pdf_output).decode()
    href = f'<a href="data:application/octet-stream;base64,{b64}" download="{filename}">Download PDF Report</a>'
    return href