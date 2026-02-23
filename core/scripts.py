import streamlit as st

def apply_vero_js():
    st.markdown("""
    <script>
        // Efeito de entrada suave nos cards
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.style.opacity = 1;
                    entry.target.style.transform = 'translateY(0)';
                }
            });
        }, { threshold: 0.1 });

        setTimeout(() => {
            const cards = window.parent.document.querySelectorAll('div[data-testid="stVerticalBlockBorderWrapper"]');
            cards.forEach(card => {
                card.style.opacity = 0;
                card.style.transform = 'translateY(30px)';
                card.style.transition = 'all 0.8s ease-out';
                observer.observe(card);
            });
        }, 500);
    </script>
    """, unsafe_allow_html=True)
