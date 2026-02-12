"""
KEMSA Upload Assistant Routes for SupplierComply
Handles CSV upload, column mapping, and Excel export to KEMSA format
"""

import io
import csv
import logging
from datetime import datetime
from flask import Blueprint, render_template, request, jsonify, send_file
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, Border, Side, PatternFill
from app import db, Product, Activity

logger = logging.getLogger(__name__)
kemsa_bp = Blueprint('kemsa', __name__, url_prefix='/kemsa')


def allowed_file(filename):
    """Check if file extension is allowed."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'csv'}


def parse_csv_file(file_stream):
    """
    Parse CSV file and return headers and rows.
    
    Args:
        file_stream: File stream from request
    
    Returns:
        Tuple (headers, rows) or (None, error_message)
    """
    try:
        # Read file content
        content = file_stream.read().decode('utf-8')
        
        # Try to detect delimiter
        sample = content[:1024]
        delimiter = ','
        if '\t' in sample:
            delimiter = '\t'
        elif ';' in sample:
            delimiter = ';'
        
        # Parse CSV
        csv_reader = csv.reader(io.StringIO(content), delimiter=delimiter)
        rows = list(csv_reader)
        
        if len(rows) < 2:
            return None, "CSV file must have at least a header row and one data row"
        
        headers = rows[0]
        data_rows = rows[1:]
        
        return headers, data_rows
        
    except Exception as e:
        logger.error(f"CSV parsing error: {str(e)}")
        return None, f"Failed to parse CSV: {str(e)}"


def validate_kemsa_data(mapped_data):
    """
    Validate data against KEMSA requirements.
    
    Args:
        mapped_data: List of dictionaries with mapped fields
    
    Returns:
        Tuple (is_valid, errors)
    """
    errors = []
    required_fields = ['product_name', 'quantity']
    
    for i, row in enumerate(mapped_data):
        row_num = i + 1
        
        # Check required fields
        for field in required_fields:
            if not row.get(field):
                errors.append(f"Row {row_num}: Missing required field '{field}'")
        
        # Validate quantity is numeric
        if row.get('quantity'):
            try:
                qty = int(row['quantity'])
                if qty < 0:
                    errors.append(f"Row {row_num}: Quantity must be positive")
            except ValueError:
                errors.append(f"Row {row_num}: Quantity must be a number")
        
        # Validate expiry date format
        if row.get('expiry_date'):
            try:
                datetime.strptime(row['expiry_date'], '%Y-%m-%d')
            except ValueError:
                errors.append(f"Row {row_num}: Expiry date must be in YYYY-MM-DD format")
    
    return len(errors) == 0, errors


def create_kemsa_excel(mapped_data, user_company_name):
    """
    Create KEMSA-formatted Excel file.
    
    Args:
        mapped_data: List of dictionaries with mapped fields
        user_company_name: Supplier company name
    
    Returns:
        BytesIO buffer with Excel file
    """
    wb = Workbook()
    ws = wb.active
    ws.title = "KEMSA Upload"
    
    # Define styles
    header_font = Font(bold=True, color="FFFFFF")
    header_fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
    header_alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    
    thin_border = Border(
        left=Side(style='thin'),
        right=Side(style='thin'),
        top=Side(style='thin'),
        bottom=Side(style='thin')
    )
    
    # KEMSA Template Headers
    kemsa_headers = [
        'Product Code',
        'Description',
        'Unit of Measure',
        'Quantity',
        'Batch Number',
        'Expiry Date',
        'GS1 Barcode Data',
        'Supplier Name',
        'Date Uploaded'
    ]
    
    # Write headers
    for col, header in enumerate(kemsa_headers, 1):
        cell = ws.cell(row=1, column=col, value=header)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = header_alignment
        cell.border = thin_border
    
    # Write data rows
    today = datetime.now().strftime('%Y-%m-%d')
    
    for row_idx, row_data in enumerate(mapped_data, 2):
        # Product Code (can be empty or mapped)
        ws.cell(row=row_idx, column=1, value=row_data.get('product_code', ''))
        
        # Description (Product Name)
        ws.cell(row=row_idx, column=2, value=row_data.get('product_name', ''))
        
        # Unit of Measure
        ws.cell(row=row_idx, column=3, value=row_data.get('unit_of_measure', 'Each'))
        
        # Quantity
        ws.cell(row=row_idx, column=4, value=row_data.get('quantity', 0))
        
        # Batch Number
        ws.cell(row=row_idx, column=5, value=row_data.get('batch_number', ''))
        
        # Expiry Date
        ws.cell(row=row_idx, column=6, value=row_data.get('expiry_date', ''))
        
        # GS1 Barcode Data
        gs1_data = row_data.get('gs1_barcode', '')
        if not gs1_data and row_data.get('gtin'):
            gs1_data = f"(01){row_data.get('gtin')}"
        ws.cell(row=row_idx, column=7, value=gs1_data)
        
        # Supplier Name
        ws.cell(row=row_idx, column=8, value=user_company_name or '')
        
        # Date Uploaded
        ws.cell(row=row_idx, column=9, value=today)
        
        # Apply borders to all cells in row
        for col in range(1, 10):
            ws.cell(row=row_idx, column=col).border = thin_border
    
    # Adjust column widths
    column_widths = [15, 40, 15, 12, 20, 15, 30, 30, 15]
    for i, width in enumerate(column_widths, 1):
        ws.column_dimensions[chr(64 + i)].width = width
    
    # Freeze header row
    ws.freeze_panes = 'A2'
    
    # Save to buffer
    buffer = io.BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    
    return buffer


def log_activity(user_id, action, details=None):
    """Log user activity."""
    try:
        activity = Activity(user_id=user_id, action=action, details=details)
        db.session.add(activity)
        db.session.commit()
    except Exception as e:
        logger.error(f"Failed to log activity: {str(e)}")
        db.session.rollback()


@kemsa_bp.route('/')
@login_required
def index():
    """Render KEMSA export page."""
    return render_template('kemsa.html')


@kemsa_bp.route('/upload', methods=['POST'])
@login_required
def upload():
    """
    Upload and parse CSV file.
    
    Returns:
        JSON with headers for column mapping
    """
    try:
        # Check if file is present
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': 'No file uploaded'}), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({'success': False, 'error': 'No file selected'}), 400
        
        # Validate file type
        if not allowed_file(file.filename):
            return jsonify({'success': False, 'error': 'Only CSV files are allowed'}), 400
        
        # Validate file size (max 5MB)
        file.seek(0, 2)  # Seek to end
        file_size = file.tell()
        file.seek(0)  # Reset to beginning
        
        if file_size > 5 * 1024 * 1024:
            return jsonify({'success': False, 'error': 'File size exceeds 5MB limit'}), 400
        
        # Parse CSV
        headers, rows = parse_csv_file(file)
        
        if headers is None:
            return jsonify({'success': False, 'error': rows}), 400
        
        # Store in session for next step
        session_key = f'kemsa_upload_{current_user.id}'
        
        # Limit preview to first 10 rows
        preview_rows = rows[:10]
        
        # Store full data in a temporary way (in production, use Redis or temp file)
        # For now, we'll store in session (limited by cookie size)
        import json
        from flask import session as flask_session
        
        flask_session[session_key] = {
            'headers': headers,
            'rows': rows[:1000],  # Limit to 1000 rows for session storage
            'total_rows': len(rows),
            'uploaded_at': datetime.utcnow().isoformat()
        }
        
        log_activity(current_user.id, 'kemsa_csv_uploaded', f'Rows: {len(rows)}')
        
        return jsonify({
            'success': True,
            'headers': headers,
            'preview_rows': preview_rows,
            'total_rows': len(rows),
            'suggested_mappings': {
                'product_name': next((h for h in headers if any(k in h.lower() for k in ['product', 'name', 'description', 'item'])), headers[0] if headers else None),
                'quantity': next((h for h in headers if any(k in h.lower() for k in ['qty', 'quantity', 'count', 'amount'])), None),
                'batch_number': next((h for h in headers if any(k in h.lower() for k in ['batch', 'lot'])), None),
                'expiry_date': next((h for h in headers if any(k in h.lower() for k in ['expiry', 'expire', 'expiration', 'date'])), None),
                'unit_of_measure': next((h for h in headers if any(k in h.lower() for k in ['unit', 'uom', 'measure'])), None),
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Upload error: {str(e)}")
        return jsonify({'success': False, 'error': 'Upload failed. Please try again.'}), 500


@kemsa_bp.route('/preview', methods=['POST'])
@login_required
def preview():
    """
    Preview mapped data before export.
    
    Request body:
        - mappings: Dictionary mapping KEMSA fields to CSV columns
    
    Returns:
        JSON with preview of mapped data and validation errors
    """
    try:
        # Check if user has uploaded data
        session_key = f'kemsa_upload_{current_user.id}'
        from flask import session as flask_session
        
        upload_data = flask_session.get(session_key)
        if not upload_data:
            return jsonify({'success': False, 'error': 'No uploaded data found. Please upload CSV first.'}), 400
        
        data = request.get_json()
        mappings = data.get('mappings', {})
        
        if not mappings:
            return jsonify({'success': False, 'error': 'Column mappings are required'}), 400
        
        headers = upload_data['headers']
        rows = upload_data['rows']
        
        # Apply mappings to create structured data
        mapped_data = []
        for row in rows:
            row_dict = {}
            for kemsa_field, csv_column in mappings.items():
                if csv_column in headers:
                    col_index = headers.index(csv_column)
                    if col_index < len(row):
                        row_dict[kemsa_field] = row[col_index].strip()
                    else:
                        row_dict[kemsa_field] = ''
                else:
                    row_dict[kemsa_field] = ''
            mapped_data.append(row_dict)
        
        # Validate data
        is_valid, errors = validate_kemsa_data(mapped_data)
        
        # Store mapped data in session
        flask_session[f'{session_key}_mapped'] = mapped_data
        
        log_activity(current_user.id, 'kemsa_data_mapped', f'Mapped fields: {list(mappings.keys())}')
        
        return jsonify({
            'success': True,
            'preview': mapped_data[:10],  # First 10 rows
            'total_rows': len(mapped_data),
            'validation': {
                'is_valid': is_valid,
                'errors': errors[:10]  # First 10 errors
            },
            'can_download': current_user.is_paid()
        }), 200
        
    except Exception as e:
        logger.error(f"Preview error: {str(e)}")
        return jsonify({'success': False, 'error': 'Preview generation failed'}), 500


@kemsa_bp.route('/download', methods=['POST'])
@login_required
def download():
    """
    Download KEMSA-formatted Excel file.
    
    Returns:
        Excel file download
    """
    try:
        # Check if user is paid
        if not current_user.is_paid():
            return jsonify({
                'success': False,
                'error': 'Excel download is a paid feature. Please upgrade to download.',
                'upgrade_required': True
            }), 403
        
        # Get mapped data from session
        session_key = f'kemsa_upload_{current_user.id}'
        from flask import session as flask_session
        
        mapped_data = flask_session.get(f'{session_key}_mapped')
        if not mapped_data:
            return jsonify({'success': False, 'error': 'No mapped data found. Please upload and map CSV first.'}), 400
        
        # Create Excel file
        excel_buffer = create_kemsa_excel(mapped_data, current_user.company_name)
        
        # Clear session data
        flask_session.pop(session_key, None)
        flask_session.pop(f'{session_key}_mapped', None)
        
        log_activity(current_user.id, 'kemsa_excel_downloaded', f'Rows: {len(mapped_data)}')
        
        # Generate filename
        filename = f"KEMSA_Export_{current_user.company_name or 'Supplier'}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        
        return send_file(
            excel_buffer,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=filename
        )
        
    except Exception as e:
        logger.error(f"Download error: {str(e)}")
        return jsonify({'success': False, 'error': 'Download failed. Please try again.'}), 500


@kemsa_bp.route('/template')
@login_required
def download_template():
    """Download empty KEMSA template."""
    try:
        wb = Workbook()
        ws = wb.active
        ws.title = "KEMSA Template"
        
        # Headers
        headers = ['Product Code', 'Description', 'Unit of Measure', 'Quantity', 'Batch Number', 'Expiry Date', 'GS1 Barcode Data']
        ws.append(headers)
        
        # Add sample row
        sample_row = ['PRD001', 'Paracetamol 500mg Tablets', 'Box of 100', '50', 'BATCH001', '2025-12-31', '(01)01234567890128']
        ws.append(sample_row)
        
        # Adjust column widths
        for i, width in enumerate([15, 40, 15, 12, 20, 15, 30], 1):
            ws.column_dimensions[chr(64 + i)].width = width
        
        buffer = io.BytesIO()
        wb.save(buffer)
        buffer.seek(0)
        
        return send_file(
            buffer,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name='KEMSA_Template.xlsx'
        )
        
    except Exception as e:
        logger.error(f"Template download error: {str(e)}")
        return jsonify({'success': False, 'error': 'Template download failed'}), 500
