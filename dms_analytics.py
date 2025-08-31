import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import mysql.connector
from sqlalchemy import create_engine
import base64
from pdf_generator import create_pdf_report, create_download_link

# Page configuration
st.set_page_config(
    page_title="DMS Analytics Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Title
st.title("📊 DMS Analytics Dashboard")
st.markdown("---")

# Database connection function
@st.cache_resource
def init_connection():
    try:
        # Replace with your actual database credentials
        db_config = {
            'host': '127.0.0.1',
            'database': 'ispsc_tagudin_dms_db',
            'user': 'root',  # Replace with your username
            'password': '',  # Replace with your password
            'port': 3306
        }
        
        engine = create_engine(f"mysql+mysqlconnector://{db_config['user']}:{db_config['password']}@{db_config['host']}:{db_config['port']}/{db_config['database']}")
        return engine
    except Exception as e:
        st.error(f"Error connecting to database: {e}")
        return None

# Load data function
@st.cache_data(ttl=3600)
def load_data():
    engine = init_connection()
    if engine is None:
        return None
    
    try:
        # Load all tables
        users_df = pd.read_sql("SELECT * FROM dms_user", engine)
        documents_df = pd.read_sql("SELECT * FROM dms_documents", engine)
        document_types_df = pd.read_sql("SELECT * FROM document_types", engine)
        departments_df = pd.read_sql("SELECT * FROM departments", engine)
        announcements_df = pd.read_sql("SELECT * FROM announcements", engine)
        notifications_df = pd.read_sql("SELECT * FROM notifications", engine)
        doc_versions_df = pd.read_sql("SELECT * FROM dms_document_versions", engine)
        doc_depts_df = pd.read_sql("SELECT * FROM document_departments", engine)
        
        # Merge documents with types
        documents_df = documents_df.merge(document_types_df, left_on='doc_type', right_on='type_id', how='left')
        
        # Merge users with departments
        users_df = users_df.merge(departments_df, left_on='department_id', right_on='department_id', how='left', suffixes=('_user', '_dept'))
        
        return {
            'users': users_df,
            'documents': documents_df,
            'announcements': announcements_df,
            'notifications': notifications_df,
            'doc_versions': doc_versions_df,
            'doc_depts': doc_depts_df,
            'departments': departments_df,
            'document_types': document_types_df
        }
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return None

# Load data
data = load_data()

if data is None:
    st.error("Could not load data. Please check your database connection.")
    st.stop()

# Sidebar filters
st.sidebar.header("Filters")
date_range = st.sidebar.date_input(
    "Select Date Range",
    value=[datetime.now().date() - timedelta(days=30), datetime.now().date()],
    max_value=datetime.now().date()
)

department_filter = st.sidebar.multiselect(
    "Filter by Department",
    options=data['departments']['name'].unique() if 'departments' in data else [],
    default=[]
)

doc_type_filter = st.sidebar.multiselect(
    "Filter by Document Type",
    options=data['document_types']['name'].unique() if 'document_types' in data else [],
    default=[]
)

# Filter data based on selections
def filter_data(df, date_col):
    if len(date_range) == 2 and date_col in df.columns:
        mask = (df[date_col] >= pd.to_datetime(date_range[0])) & (df[date_col] <= pd.to_datetime(date_range[1]))
        return df.loc[mask]
    return df

# Safely filter data
filtered_docs = filter_data(data['documents'], 'created_at') if 'documents' in data else pd.DataFrame()
filtered_announcements = filter_data(data['announcements'], 'created_at') if 'announcements' in data else pd.DataFrame()
filtered_notifications = filter_data(data['notifications'], 'created_at') if 'notifications' in data else pd.DataFrame()

if department_filter and 'documents' in data and 'department_id' in data['documents'].columns:
    dept_ids = data['departments'][data['departments']['name'].isin(department_filter)]['department_id']
    filtered_docs = filtered_docs[filtered_docs['department_id'].isin(dept_ids)]

if doc_type_filter and 'name' in filtered_docs.columns:
    filtered_docs = filtered_docs[filtered_docs['name'].isin(doc_type_filter)]

# Metrics row
st.subheader("Key Metrics")
col1, col2, col3, col4 = st.columns(4)

with col1:
    total_docs = len(data['documents']) if 'documents' in data else 0
    st.metric("Total Documents", total_docs)

with col2:
    total_users = len(data['users']) if 'users' in data else 0
    st.metric("Total Users", total_users)

with col3:
    if 'documents' in data and 'status' in data['documents'].columns:
        active_docs = len(data['documents'][data['documents']['status'] == 'active'])
    else:
        active_docs = 0
    st.metric("Active Documents", active_docs)

with col4:
    total_announcements = len(data['announcements']) if 'announcements' in data else 0
    st.metric("Total Announcements", total_announcements)

# Charts and visualizations
st.markdown("---")
st.subheader("Visualizations")

# Create tabs for different chart types
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "Documents Overview", 
    "User Analytics", 
    "Department Analysis", 
    "Timeline Analysis",
    "Raw Data"
])

with tab1:
    if not filtered_docs.empty:
        col1, col2 = st.columns(2)
        
        with col1:
            # Documents by type
            if 'name' in filtered_docs.columns:
                doc_type_counts = filtered_docs['name'].value_counts()
                fig = px.pie(
                    values=doc_type_counts.values, 
                    names=doc_type_counts.index, 
                    title='Documents by Type'
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Document type data not available")
        
        with col2:
            # Documents status
            if 'status' in filtered_docs.columns:
                status_counts = filtered_docs['status'].value_counts()
                fig = px.bar(
                    x=status_counts.index, 
                    y=status_counts.values,
                    title='Documents by Status',
                    labels={'x': 'Status', 'y': 'Count'}
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Status data not available")
        
        # Documents over time
        if 'created_at' in filtered_docs.columns:
            docs_over_time = filtered_docs.groupby(pd.Grouper(key='created_at', freq='D')).size().reset_index(name='count')
            if not docs_over_time.empty:
                fig = px.line(
                    docs_over_time, 
                    x='created_at', 
                    y='count',
                    title='Documents Created Over Time'
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No document creation data available for the selected period")
        else:
            st.info("Creation date data not available")
    else:
        st.info("No document data available for the selected filters")

with tab2:
    if 'users' in data and not data['users'].empty:
        col1, col2 = st.columns(2)
        
        with col1:
            # Users by role
            if 'role' in data['users'].columns:
                role_counts = data['users']['role'].value_counts()
                fig = px.pie(
                    values=role_counts.values, 
                    names=role_counts.index, 
                    title='Users by Role'
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Role data not available")
        
        with col2:
            # Users by status
            if 'status' in data['users'].columns:
                status_counts = data['users']['status'].value_counts()
                fig = px.bar(
                    x=status_counts.index, 
                    y=status_counts.values,
                    title='Users by Status',
                    labels={'x': 'Status', 'y': 'Count'}
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Status data not available")
        
        # Users by department
        if 'name' in data['users'].columns:
            user_dept_counts = data['users']['name'].value_counts()
            fig = px.bar(
                x=user_dept_counts.index, 
                y=user_dept_counts.values,
                title='Users by Department',
                labels={'x': 'Department', 'y': 'Count'}
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Department data not available for users")
    else:
        st.info("No user data available")

with tab3:
    if not filtered_docs.empty and 'departments' in data:
        # Department document counts
        if 'department_id' in filtered_docs.columns:
            dept_docs = filtered_docs.merge(data['departments'], left_on='department_id', right_on='department_id', how='left')
            if 'name_y' in dept_docs.columns:
                dept_counts = dept_docs['name_y'].value_counts()
                
                fig = px.bar(
                    x=dept_counts.index, 
                    y=dept_counts.values,
                    title='Documents by Department',
                    labels={'x': 'Department', 'y': 'Count'}
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Could not merge department data")
        else:
            st.info("Department ID not found in documents")
    else:
        st.info("No department data available")

with tab4:
    # Documents timeline
    if not filtered_docs.empty and 'created_at' in filtered_docs.columns and 'title' in filtered_docs.columns:
        docs_timeline = filtered_docs[['title', 'created_at', 'name']].copy()
        docs_timeline['date'] = docs_timeline['created_at'].dt.date
        
        fig = px.timeline(
            docs_timeline, 
            x_start="created_at", 
            x_end=docs_timeline['created_at'] + pd.Timedelta(hours=1),
            y="title", 
            color="name",
            title="Document Creation Timeline"
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No timeline data available for documents")
    
    # Announcements timeline
    if not filtered_announcements.empty and 'created_at' in filtered_announcements.columns and 'title' in filtered_announcements.columns:
        ann_timeline = filtered_announcements[['title', 'created_at', 'status']].copy()
        fig = px.timeline(
            ann_timeline, 
            x_start="created_at", 
            x_end=ann_timeline['created_at'] + pd.Timedelta(hours=1),
            y="title", 
            color="status",
            title="Announcements Timeline"
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No timeline data available for announcements")

with tab5:
    st.subheader("Documents Data")
    if not filtered_docs.empty:
        display_cols = [col for col in ['doc_id', 'title', 'name', 'status', 'created_at', 'created_by_name'] if col in filtered_docs.columns]
        st.dataframe(
            filtered_docs[display_cols],
            use_container_width=True
        )
    else:
        st.info("No document data available")
    
    st.subheader("Users Data")
    if 'users' in data and not data['users'].empty:
        display_cols = [col for col in ['user_id', 'Username', 'firstname', 'lastname', 'role', 'status', 'name'] if col in data['users'].columns]
        st.dataframe(
            data['users'][display_cols],
            use_container_width=True
        )
    else:
        st.info("No user data available")

# Additional analytics
st.markdown("---")
st.subheader("Advanced Analytics")

# Document version analysis
if st.checkbox("Show Document Version Analysis"):
    if 'doc_versions' in data and not data['doc_versions'].empty:
        version_counts = data['doc_versions'].groupby('doc_id').size().reset_index(name='version_count')
        fig = px.histogram(
            version_counts, 
            x='version_count',
            title='Distribution of Document Versions',
            labels={'version_count': 'Number of Versions'}
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No version data available")

# User activity analysis
if st.checkbox("Show User Activity Analysis"):
    if not filtered_docs.empty and 'created_by_name' in filtered_docs.columns:
        user_doc_counts = filtered_docs['created_by_name'].value_counts().reset_index()
        user_doc_counts.columns = ['user', 'document_count']
        
        fig = px.bar(
            user_doc_counts.head(10), 
            x='user', 
            y='document_count',
            title='Top 10 Users by Document Creation',
            labels={'user': 'User', 'document_count': 'Documents Created'}
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No user activity data available")

# Export options
st.sidebar.markdown("---")
st.sidebar.subheader("Export Options")

# CSV Export
if st.sidebar.button("Export Documents Data as CSV"):
    if not filtered_docs.empty:
        csv = filtered_docs.to_csv(index=False)
        st.sidebar.download_button(
            label="Download CSV",
            data=csv,
            file_name="documents_data.csv",
            mime="text/csv"
        )
    else:
        st.sidebar.warning("No document data to export")

if st.sidebar.button("Export Users Data as CSV"):
    if 'users' in data and not data['users'].empty:
        csv = data['users'].to_csv(index=False)
        st.sidebar.download_button(
            label="Download CSV",
            data=csv,
            file_name="users_data.csv",
            mime="text/csv"
        )
    else:
        st.sidebar.warning("No user data to export")

# PDF Export with customization options
st.sidebar.markdown("---")
st.sidebar.subheader("PDF Report Customization")

# PDF customization options
include_detailed_table = st.sidebar.checkbox("Include Detailed Table", value=True)
report_title = st.sidebar.text_input("Report Title", "DMS Analytics Report")

if st.sidebar.button("Generate PDF Report"):
    with st.spinner("Generating PDF report..."):
        try:
            # Create PDF with custom options
            pdf = create_pdf_report(data, filtered_docs, date_range, department_filter, doc_type_filter)
            
            # Save PDF to bytes buffer
            pdf_output = pdf.output(dest='S').encode('latin1', 'replace')
            
            # Create download link
            st.sidebar.markdown(create_download_link(pdf_output, f"{report_title.replace(' ', '_')}.pdf"), unsafe_allow_html=True)
            
            st.sidebar.success("PDF report generated successfully!")
            
        except Exception as e:
            st.sidebar.error(f"Error generating PDF: {e}")

# Footer
st.markdown("---")
st.caption("DMS Analytics Dashboard - Generated on " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))