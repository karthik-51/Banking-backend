

from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib import colors
import io
import json
from datetime import datetime
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.ticker import MaxNLocator
import numpy as np

# Load alert history
HARDWARE_ALERTS_HISTORY = {}
SOFTWARE_ALERTS_HISTORY = {}

try:
    with open('hardware_alerts_history.json', 'r') as f:
        HARDWARE_ALERTS_HISTORY = json.load(f)
    with open('software_alerts_history.json', 'r') as f:
        SOFTWARE_ALERTS_HISTORY = json.load(f)
    print("Alert history JSON files loaded successfully.")
except FileNotFoundError:
    print("Warning: Alert history JSON files not found.")# Helper function to filter alerts by date range
def filter_alerts_by_date(alerts, from_date_str, to_date_str):
    """
    Filters a list of alerts based on a specified date range.

    Args:
        alerts (list): A list of alert dictionaries, each containing 'timestamp'.
        from_date_str (str): Start date string in 'YYYY-MM-DD' format. Can be None.
        to_date_str (str): End date string in 'YYYY-MM-DD' format. Can be None.

    Returns:
        list: A new list containing only the alerts within the specified date range.
    """
    if not alerts:
        return []

    from_date = None
    to_date = None

    if from_date_str:
        from_date = datetime.strptime(from_date_str, '%Y-%m-%d')
    if to_date_str:
        to_date = datetime.strptime(to_date_str, '%Y-%m-%d')

    filtered = []
    for alert in alerts:
        try:
            # Attempt to parse timestamp in ISO format first, then fallback to another
            alert_date = datetime.strptime(alert['timestamp'], '%Y-%m-%dT%H:%M:%S.%fZ')
        except ValueError:
            try:
                alert_date = datetime.strptime(alert['timestamp'], '%Y-%m-%d %H:%M:%S')
            except ValueError:
                print(f"Warning: Could not parse timestamp: {alert['timestamp']}")
                continue # Skip this alert if timestamp is unparseable

        if from_date and alert_date < from_date:
            continue
        if to_date:
            # Include the whole day for 'to' date by setting time to end of day
            to_end = to_date.replace(hour=23, minute=59, second=59, microsecond=999999)
            if alert_date > to_end:
                continue
        filtered.append(alert)
    return filtered

# Helper function to get status counts for alerts
def get_status_counts(alerts):
    """
    Calculates the count of 'Healthy', 'Warning', and 'Critical' alerts.

    Args:
        alerts (list): A list of alert dictionaries, each containing 'status'.

    Returns:
        dict: A dictionary with counts for each status.
    """
    counts = {"Healthy": 0, "Warning": 0, "Critical": 0}
    for alert in alerts:
        counts[alert['status']] = counts.get(alert['status'], 0) + 1
    return counts

# Helper function to generate and save chart image to a BytesIO buffer
def generate_chart_image(chart_type, labels, data_sets, title, width_inches=6, height_inches=3):
    # Use professional style
    #plt.style.use('seaborn-whitegrid')
    sns.set_style("whitegrid")
    
    # Create figure with constrained layout
    fig, ax = plt.subplots(figsize=(width_inches, height_inches), facecolor='white', layout='constrained')
    
    # Professional color palette (consistent with first code)
    status_colors = {
        "Critical": "#e74c3c",   # Red
        "Warning": "#f39c12",     # Orange
        "Healthy": "#2ecc71"      # Green
    }
    
    # Set professional fonts
    plt.rcParams['font.family'] = 'DejaVu Sans'  # Use a common professional font
    plt.rcParams['font.size'] = 9
    plt.rcParams['axes.titlesize'] = 12
    plt.rcParams['axes.labelsize'] = 10
    plt.rcParams['xtick.labelsize'] = 8
    plt.rcParams['ytick.labelsize'] = 8
    plt.rcParams['legend.fontsize'] = 9

    if chart_type == "bar":
        # Handle grouped bars for Warning/Critical breakdown
        if len(data_sets) > 1 and "label" in data_sets[0]:
            bar_width = 0.35
            x = np.arange(len(labels))
            rects = []  # Store bars for labeling
            
            for i, dataset in enumerate(data_sets):
                # Map status to professional colors
                color = status_colors.get(dataset["label"], dataset.get("backgroundColor", "#3498db"))
                r = ax.bar(
                    x + (i - (len(data_sets)-1)/2) * bar_width, 
                    dataset["data"], 
                    bar_width, 
                    label=dataset["label"], 
                    color=color,
                    edgecolor='white',
                    linewidth=0.7
                )
                rects.append(r)
                
            # Add value labels on top of bars
            for rect_group in rects:
                for rect in rect_group:
                    height = rect.get_height()
                    if height > 0:  # Only show label if value > 0
                        ax.annotate(f'{height}',
                            xy=(rect.get_x() + rect.get_width() / 2, height),
                            xytext=(0, 3),  # 3 points vertical offset
                            textcoords="offset points",
                            ha='center', va='bottom',
                            fontsize=8)
            
            ax.set_xticks(x)
            ax.set_xticklabels(labels, rotation=45, ha="right", fontsize=9)
            
            # Add legend with professional styling
            ax.legend(
                loc="upper center", 
                bbox_to_anchor=(0.5, -0.15), 
                ncol=len(data_sets),
                frameon=True,
                fancybox=True,
                shadow=True,
                framealpha=0.8
            )
        else: 
            # Single bar chart
            colors = [status_colors.get(label, "#3498db") for label in labels]
            bars = ax.bar(
                labels, 
                data_sets[0]["data"], 
                color=colors,
                edgecolor='white',
                linewidth=0.7
            )
            
            # Add value labels on top of bars
            for bar in bars:
                height = bar.get_height()
                if height > 0:  # Only show label if value > 0
                    ax.annotate(f'{height}',
                        xy=(bar.get_x() + bar.get_width() / 2, height),
                        xytext=(0, 3),  # 3 points vertical offset
                        textcoords="offset points",
                        ha='center', va='bottom',
                        fontsize=8)
        
        # Professional touches for bar charts
        ax.set_ylabel('Number of Alerts', fontsize=10, labelpad=10)
        ax.yaxis.set_major_locator(MaxNLocator(integer=True))
        ax.grid(True, linestyle='--', alpha=0.6, axis='y')
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        
    elif chart_type == "pie":
        # Map labels to professional colors
        colors = [status_colors.get(label, "#3498db") for label in labels]
        
        # Create pie chart with professional settings
        wedges, texts, autotexts = ax.pie(
            data_sets[0]["data"], 
            labels=labels, 
            autopct='%1.1f%%',
            startangle=90,
            colors=colors,
            wedgeprops={'edgecolor': 'white', 'linewidth': 0.7},
            textprops={'fontsize': 9, 'color': 'black'},
            pctdistance=0.85
        )
        
        # Improve percentage text
        for autotext in autotexts:
            autotext.set_color('white')
            autotext.set_fontsize(8)
            autotext.set_fontweight('bold')
        
        # Add legend with professional styling
        ax.legend(
            wedges, 
            labels,
            title="Status",
            loc="center left",
            bbox_to_anchor=(1, 0, 0.5, 1),
            frameon=True,
            fancybox=True,
            shadow=True,
            framealpha=0.8
        )
        
        # Equal aspect ratio ensures pie is circular
        ax.axis('equal')  

    # Common professional touches for all charts
    ax.set_title(title, fontsize=12, pad=15, fontweight='bold')
    ax.title.set_position([0.5, 1.05])
    
    # Adjust layout and save
    plt.tight_layout(pad=2.0)
    
    # Save chart to BytesIO object
    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=150, bbox_inches='tight', transparent=False)
    buf.seek(0)
    plt.close(fig)
    return buf

def generate_pdf_report(bank_name, from_date_str, to_date_str):
    """
    Generates a PDF performance report for a given bank and date range.

    Args:
        bank_name (str): The name of the bank for which to generate the report.
        from_date_str (str): Start date string in 'YYYY-MM-DD' format. Can be None.
        to_date_str (str): End date string in 'YYYY-MM-DD' format. Can be None.

    Returns:
        tuple: A tuple containing (io.BytesIO buffer, error_message_str).
               Returns (None, error_message) if bank_name is not provided.
    """
    if not bank_name:
        return None, "Bank name not provided."

    # Get all alerts for the selected bank from the pre-loaded data
    all_hardware_alerts = HARDWARE_ALERTS_HISTORY.get(bank_name, [])
    all_software_alerts = SOFTWARE_ALERTS_HISTORY.get(bank_name, [])

    # Filter alerts based on the provided date range
    filtered_hardware_alerts = filter_alerts_by_date(all_hardware_alerts, from_date_str, to_date_str)
    filtered_software_alerts = filter_alerts_by_date(all_software_alerts, from_date_str, to_date_str)

    hardware_status_counts = get_status_counts(filtered_hardware_alerts)
    software_status_counts = get_status_counts(filtered_software_alerts)

    total_hardware_alerts = len(filtered_hardware_alerts)
    total_software_alerts = len(filtered_software_alerts)

    # --- Generate Chart Images on Backend using Matplotlib ---
    chart_buffers = {}

    # Hardware Bar Chart
    hardware_bar_labels = ["Warning", "Critical"]
    hardware_bar_data = [{"data": [hardware_status_counts.get("Warning", 0), hardware_status_counts.get("Critical", 0)], "backgroundColor": ["#facc15", "#ef4444"]}]
    chart_buffers['hardwareBar'] = generate_chart_image(
        "bar", hardware_bar_labels, hardware_bar_data, "Hardware Alerts Summary"
    )

    # Hardware Pie Chart
    hardware_pie_labels = ["Warning", "Critical"]
    hardware_pie_data = [{"data": [hardware_status_counts.get("Warning", 0), hardware_status_counts.get("Critical", 0)], "backgroundColor": ["#facc15", "#ef4444"]}]
    chart_buffers['hardwarePie'] = generate_chart_image(
        "pie", hardware_pie_labels, hardware_pie_data, "Hardware Status Distribution"
    )

    # ATM-wise Breakdown Chart
    atms = sorted(list(set(a['atm'] for a in filtered_hardware_alerts if 'atm' in a)))
    atm_warning_data = [len([a for a in filtered_hardware_alerts if a.get('atm') == atm and a['status'] == 'Warning']) for atm in atms]
    atm_critical_data = [len([a for a in filtered_hardware_alerts if a.get('atm') == atm and a['status'] == 'Critical']) for atm in atms]
    if atms: # Only generate if there are ATMs
        atm_breakdown_data = [
            {"label": "Warning", "data": atm_warning_data, "backgroundColor": "#facc15"},
            {"label": "Critical", "data": atm_critical_data, "backgroundColor": "#ef4444"}
        ]
        chart_buffers['atmBreakdown'] = generate_chart_image(
            "bar", atms, atm_breakdown_data, "ATM-wise Hardware Alerts"
        )

    # Software Bar Chart
    software_bar_labels = ["Warning", "Critical"]
    software_bar_data = [{"data": [software_status_counts.get("Warning", 0), software_status_counts.get("Critical", 0)], "backgroundColor": ["#f97316", "#dc2626"]}]
    chart_buffers['softwareBar'] = generate_chart_image(
        "bar", software_bar_labels, software_bar_data, "Software Alerts Summary"
    )

    # Software Pie Chart
    software_pie_labels = ["Warning", "Critical"]
    software_pie_data = [{"data": [software_status_counts.get("Warning", 0), software_status_counts.get("Critical", 0)], "backgroundColor": ["#f97316", "#dc2626"]}]
    chart_buffers['softwarePie'] = generate_chart_image(
        "pie", software_pie_labels, software_pie_data, "Software Status Distribution"
    )

    # Software-System Breakdown Chart
    sw_keys_unique = sorted(list(set(f"{a['software']} - {a['system']}" for a in filtered_software_alerts if 'software' in a and 'system' in a)))
    sw_warning_data = [len([a for a in filtered_software_alerts if f"{a.get('software')} - {a.get('system')}" == key and a['status'] == 'Warning']) for key in sw_keys_unique]
    sw_critical_data = [len([a for a in filtered_software_alerts if f"{a.get('software')} - {a.get('system')}" == key and a['status'] == 'Critical']) for key in sw_keys_unique]
    if sw_keys_unique: # Only generate if there are software systems
        sw_breakdown_data = [
            {"label": "Warning", "data": sw_warning_data, "backgroundColor": "#f97316"},
            {"label": "Critical", "data": sw_critical_data, "backgroundColor": "#dc2626"}
        ]
        chart_buffers['swSystemBreakdown'] = generate_chart_image(
            "bar", sw_keys_unique, sw_breakdown_data, "Software-System Alerts Breakdown"
        )


    # --- ReportLab PDF Generation ---
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()

    # Custom styles for the report
    title_style = ParagraphStyle(
        'TitleStyle',
        parent=styles['h1'],
        fontSize=28, # Increased font size
        leading=34,  # Increased leading
        alignment=TA_CENTER,
        spaceAfter=18, # Increased space
        textColor=colors.HexColor('#00188c') # Dark blue from frontend
    )
    heading_style = ParagraphStyle(
        'HeadingStyle',
        parent=styles['h2'],
        fontSize=20, # Increased font size
        leading=26,  # Increased leading
        spaceAfter=12,
        spaceBefore=25, # Increased space
        textColor=colors.HexColor('#00188c') # Dark blue from frontend
    )
    subheading_style = ParagraphStyle(
        'SubheadingStyle',
        parent=styles['h3'],
        fontSize=16, # Increased font size
        leading=20,  # Increased leading
        spaceAfter=10,
        spaceBefore=15, # Increased space
        textColor=colors.HexColor('#232323') # Dark grey from frontend
    )
    normal_style = styles['Normal']
    normal_style.fontSize = 11 # Increased font size
    normal_style.leading = 16  # Increased leading
    normal_style.alignment = TA_LEFT # Changed to left for general text

    centered_normal_style = ParagraphStyle(
        'CenteredNormalStyle',
        parent=normal_style,
        alignment=TA_CENTER # For summary text below charts
    )
    
    list_item_style = ParagraphStyle(
        'ListItemStyle',
        parent=normal_style,
        spaceBefore=3,
        spaceAfter=3,
        leftIndent=20
    )


    story = []

    # --- Report Header ---
    story.append(Paragraph("Monthly Performance Report", title_style))
    story.append(Paragraph(f"<b>For:</b> {bank_name}", subheading_style))
    
    date_range_text = "All Available Data"
    if from_date_str and to_date_str:
        date_range_text = f"{datetime.strptime(from_date_str, '%Y-%m-%d').strftime('%B %d, %Y')} to {datetime.strptime(to_date_str, '%Y-%m-%d').strftime('%B %d, %Y')}"
    elif from_date_str:
        date_range_text = f"From {datetime.strptime(from_date_str, '%Y-%m-%d').strftime('%B %d, %Y')} to Current Date"
    elif to_date_str:
        date_range_text = f"From Start to {datetime.strptime(to_date_str, '%Y-%m-%d').strftime('%B %d, %Y')}"
    
    story.append(Paragraph(f"<b>Date Range:</b> {date_range_text}", subheading_style))
    story.append(Spacer(1, 20)) # More space

    # --- Summary Section ---
    story.append(Paragraph("<u>Alert Summary</u>", heading_style))
    story.append(Paragraph(f"Total Hardware Alerts: <b>{total_hardware_alerts}</b> (Warning: {hardware_status_counts.get('Warning', 0)}, Critical: {hardware_status_counts.get('Critical', 0)})", normal_style))
    story.append(Paragraph(f"Total Software Alerts: <b>{total_software_alerts}</b> (Warning: {software_status_counts.get('Warning', 0)}, Critical: {software_status_counts.get('Critical', 0)})", normal_style))
    story.append(Spacer(1, 30)) # More space

    # --- Charts Section ---
    story.append(Paragraph("<u>Visual Analytics</u>", heading_style))
    story.append(Spacer(1, 10))

    # Hardware Charts
    story.append(Paragraph("<b>Hardware Alert Visuals:</b>", subheading_style))
    if 'hardwareBar' in chart_buffers:
        story.append(Image(chart_buffers['hardwareBar'], width=500, height=280)) # Larger image
        story.append(Paragraph("Hardware Alerts Summary (Bar Chart)", centered_normal_style))
        story.append(Spacer(1, 15))
    if 'hardwarePie' in chart_buffers:
        story.append(Image(chart_buffers['hardwarePie'], width=350, height=200)) # Larger image
        story.append(Paragraph("Hardware Status Distribution (Pie Chart)", centered_normal_style))
        story.append(Spacer(1, 15))
    if 'atmBreakdown' in chart_buffers:
        story.append(Image(chart_buffers['atmBreakdown'], width=550, height=300)) # Larger image
        story.append(Paragraph("ATM-wise Hardware Alerts Breakdown", centered_normal_style))
        story.append(Spacer(1, 15))
    story.append(Spacer(1, 30))

    # Software Charts
    story.append(Paragraph("<b>Software Alert Visuals:</b>", subheading_style))
    if 'softwareBar' in chart_buffers:
        story.append(Image(chart_buffers['softwareBar'], width=500, height=280))
        story.append(Paragraph("Software Alerts Summary (Bar Chart)", centered_normal_style))
        story.append(Spacer(1, 15))
    if 'softwarePie' in chart_buffers:
        story.append(Image(chart_buffers['softwarePie'], width=350, height=200))
        story.append(Paragraph("Software Status Distribution (Pie Chart)", centered_normal_style))
        story.append(Spacer(1, 15))
    if 'swSystemBreakdown' in chart_buffers:
        story.append(Image(chart_buffers['swSystemBreakdown'], width=550, height=300))
        story.append(Paragraph("Software-System Alerts Breakdown", centered_normal_style))
        story.append(Spacer(1, 15))
    story.append(Spacer(1, 30))

    doc.build(story)
    buffer.seek(0)
    return buffer, None