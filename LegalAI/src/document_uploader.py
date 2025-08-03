import streamlit as st
import os
import tempfile
from pathlib import Path
import sys

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from court_classifier import ImprovedCourtClassifier

class DocumentUploader:
    def __init__(self):
        self.classifier = ImprovedCourtClassifier()
        self.upload_dir = "uploads/pending"
        Path(self.upload_dir).mkdir(parents=True, exist_ok=True)
    
    def display_upload_interface(self):
        """Display the document upload interface in Streamlit"""
        
        st.header("📄 Document Upload & Organization")
        
        # Upload section
        with st.expander("Upload New Documents", expanded=True):
            uploaded_files = st.file_uploader(
                "Choose legal documents to upload",
                type=['pdf', 'txt', 'doc', 'docx'],
                accept_multiple_files=True,
                help="Upload legal documents (PDFs, text files) to automatically organize them by court"
            )
            
            if uploaded_files:
                if st.button("🔄 Process & Organize Documents"):
                    self._process_uploads(uploaded_files)
        
        # Manual organization section
        with st.expander("Manual Document Organization"):
            st.write("Organize existing documents in your database")
            
            if st.button("🔍 Scan & Organize Existing Documents"):
                self._organize_existing_documents()
        
        # Database status
        self._display_database_status()
    
    def _process_uploads(self, uploaded_files):
        """Process uploaded files and organize them"""
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        results = []
        
        for i, uploaded_file in enumerate(uploaded_files):
            status_text.text(f"Processing {uploaded_file.name}...")
            
            # Save uploaded file temporarily
            with tempfile.NamedTemporaryFile(delete=False, suffix=f".{uploaded_file.name.split('.')[-1]}") as tmp_file:
                tmp_file.write(uploaded_file.getvalue())
                tmp_path = tmp_file.name
            
            try:
                # Classify and organize
                final_path = self.classifier.organize_document(tmp_path)
                results.append({
                    'filename': uploaded_file.name,
                    'status': 'success',
                    'path': final_path
                })
            except Exception as e:
                results.append({
                    'filename': uploaded_file.name,
                    'status': 'error',
                    'error': str(e)
                })
            
            progress_bar.progress((i + 1) / len(uploaded_files))
        
        # Display results
        status_text.text("Processing complete!")
        
        success_count = sum(1 for r in results if r['status'] == 'success')
        st.success(f"✅ Successfully organized {success_count}/{len(results)} documents")
        
        # Show details
        for result in results:
            if result['status'] == 'success':
                st.write(f"📁 {result['filename']} → {result['path']}")
            else:
                st.error(f"❌ {result['filename']}: {result['error']}")
    
    def _organize_existing_documents(self):
        """Organize documents that are already in the database"""
        
        # Look for misplaced documents
        supreme_court_dir = "database/cases/nys/supreme_court"
        
        if not os.path.exists(supreme_court_dir):
            st.warning("No existing documents found to organize")
            return
        
        files_to_organize = []
        for filename in os.listdir(supreme_court_dir):
            if filename.endswith('.pdf'):
                file_path = os.path.join(supreme_court_dir, filename)
                court_type, confidence = self.classifier.classify_document(file_path)
                
                # If classified as something other than supreme_court with good confidence
                if court_type != 'supreme_court' and confidence > 0.5:
                    files_to_organize.append({
                        'filename': filename,
                        'current_path': file_path,
                        'suggested_court': court_type,
                        'confidence': confidence
                    })
        
        if not files_to_organize:
            st.success("✅ All documents are correctly organized!")
            return
        
        st.write(f"Found {len(files_to_organize)} documents that may be misclassified:")
        
        # Show suggestions
        for item in files_to_organize:
            with st.container():
                col1, col2, col3 = st.columns([3, 2, 1])
                
                with col1:
                    st.write(f"📄 {item['filename'][:50]}...")
                
                with col2:
                    st.write(f"→ {item['suggested_court']} ({item['confidence']:.2f})")
                
                with col3:
                    if st.button("✅ Move", key=f"move_{item['filename']}"):
                        try:
                            new_path = self.classifier.organize_document(item['current_path'])
                            st.success(f"Moved to {new_path}")
                            st.experimental_rerun()
                        except Exception as e:
                            st.error(f"Error: {e}")
    
    def _display_database_status(self):
        """Display current database organization status"""
        
        st.subheader("📊 Database Status")
        
        base_dirs = [
            "database/cases/nys",
            "database/cases/federal",
            "database/statutes",
            "database/regulations"
        ]
        
        total_docs = 0
        
        for base_dir in base_dirs:
            if os.path.exists(base_dir):
                for root, dirs, files in os.walk(base_dir):
                    pdf_count = len([f for f in files if f.endswith('.pdf')])
                    txt_count = len([f for f in files if f.endswith('.txt')])
                    
                    if pdf_count > 0 or txt_count > 0:
                        rel_path = os.path.relpath(root, "database")
                        st.write(f"📁 {rel_path}: {pdf_count} PDFs, {txt_count} text files")
                        total_docs += pdf_count + txt_count
        
        st.metric("Total Documents", total_docs)

# Test function
def test_upload_system():
    """Test the upload system"""
    uploader = DocumentUploader()
    print("🧪 Testing Document Upload System")
    print("-" * 50)
    
    # Test classification of existing documents
    test_dir = "database/cases/nys/supreme_court"
    if os.path.exists(test_dir):
        for filename in os.listdir(test_dir)[:3]:
            if filename.endswith('.pdf'):
                file_path = os.path.join(test_dir, filename)
                court_type, confidence = uploader.classifier.classify_document(file_path)
                print(f"📄 {filename}")
                print(f"   Classification: {court_type} ({confidence:.2f})")

if __name__ == "__main__":
    test_upload_system()

# Alias for compatibility
ImprovedCourtClassifier = ImprovedCourtClassifier

# Alias for compatibility
EnhancedCourtClassifier = ImprovedCourtClassifier
