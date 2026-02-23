import streamlit as st

def apply_vero_js():
    # Injeta scripts para animações de entrada e efeitos de mouse
    st.markdown("""
    <script>
        // 1. Efeito de Revelação (Fade-in) ao carregar a página
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.style.opacity = 1;
                    entry.target.style.transform = 'translateY(0)';
                }
            });
        });

        // Aplica o efeito em todos os cards arredondados
        window.addEventListener('load', () => {
            const cards = parent.document.querySelectorAll('div[data-testid="stVerticalBlockBorderWrapper"]');
            cards.forEach(card => {
                card.style.opacity = 0;
                card.style.transform = 'translateY(20px)';
                card.style.transition = 'all 0.6s cubic-bezier(0.22, 1, 0.36, 1)';
                observer.observe(card);
            });
        });

        // 2. Feedback Sonoro Sutil ao clicar em botões (Opcional)
        function playClick() {
            const audio = new Audio('https://www.soundjay.com/buttons/sounds/button-16.mp3');
            audio.volume = 0.2;
            audio.play();
        }
    </script>
    """, unsafe_allow_html=True)
