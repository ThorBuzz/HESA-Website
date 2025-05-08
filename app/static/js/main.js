/* Main JavaScript for HESA KNUST Website */

document.addEventListener('DOMContentLoaded', function() {
    // Mobile navigation toggle
    const mobileMenuBtn = document.querySelector('.mobile-menu-btn');
    const nav = document.querySelector('.nav');
    const header = document.querySelector('.header');

    if (mobileMenuBtn && nav) {
        mobileMenuBtn.addEventListener('click', function() {
            // Toggle menu button animation
            this.classList.toggle('active');
            
            // Toggle navigation visibility
            nav.classList.toggle('active');
            
            // Toggle header background
            if (this.classList.contains('active')) {
                header.style.backgroundColor = '#ffffff';
                header.style.boxShadow = '0 2px 10px rgba(0,0,0,0.1)';
            } else {
                header.style.backgroundColor = 'transparent';
                header.style.boxShadow = 'none';
            }
        });
    }

    // Navbar scroll effect
    window.addEventListener('scroll', function() {
        const header = document.querySelector('.header');
        if (window.scrollY > 50) {
            header.classList.add('scrolled');
        } else {
            header.classList.remove('scrolled');
        }
    });

    // Progress bar
    function updateProgressBar() {
        const scrollProgress = (window.scrollY / (document.documentElement.scrollHeight - window.innerHeight)) * 100;
        const progressBar = document.getElementById('progressBar');
        if (progressBar) {
            progressBar.style.width = scrollProgress + '%';
        }
    }

    window.addEventListener('scroll', updateProgressBar);

    // Intersection Observer for animations
    const animatedElements = document.querySelectorAll('.awareness-card, .entertainment-card, .blog-card, .article, .comments-section');
    
    if (animatedElements.length > 0) {
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('visible');
                }
            });
        }, { threshold: 0.1 });

        animatedElements.forEach(el => {
            observer.observe(el);
        });
    }

    // Section navigation dots
    const sections = document.querySelectorAll('section[id]');
    const sectionNav = document.getElementById('sectionNav');
    
    if (sections.length > 0 && sectionNav) {
        // Create navigation dots
        sections.forEach((section, index) => {
            const dot = document.createElement('div');
            dot.className = 'nav-dot';
            dot.addEventListener('click', () => {
                section.scrollIntoView({ behavior: 'smooth' });
            });
            sectionNav.appendChild(dot);
        });

        // Update active dot on scroll
        window.addEventListener('scroll', () => {
            const scrollPosition = window.scrollY + window.innerHeight / 2;
            
            sections.forEach((section, index) => {
                const dot = document.querySelectorAll('.nav-dot')[index];
                const sectionTop = section.offsetTop;
                const sectionBottom = sectionTop + section.offsetHeight;

                if (scrollPosition >= sectionTop && scrollPosition < sectionBottom) {
                    dot.classList.add('active');
                } else {
                    dot.classList.remove('active');
                }
            });
        });
    }

    // Form validation
    const forms = document.querySelectorAll('form');
    
    forms.forEach(form => {
        const submitButton = form.querySelector('button[type="submit"]');
        
        if (submitButton) {
            form.addEventListener('submit', function(e) {
                if (!form.checkValidity()) {
                    e.preventDefault();
                    
                    // Find invalid fields
                    const invalidFields = form.querySelectorAll(':invalid');
                    
                    // Add error class and show error message
                    invalidFields.forEach(field => {
                        field.classList.add('is-invalid');
                        
                        // Find parent form-group
                        const formGroup = field.closest('.form-group');
                        if (formGroup) {
                            const errorMsg = formGroup.querySelector('.invalid-feedback') || formGroup.querySelector('.error-message');
                            if (errorMsg) {
                                errorMsg.style.display = 'block';
                            }
                        }
                    });
                    
                    // Scroll to first invalid field
                    if (invalidFields.length > 0) {
                        invalidFields[0].scrollIntoView({ behavior: 'smooth', block: 'center' });
                        invalidFields[0].focus();
                    }
                }
            });
        }
    });

    // Initialize image upload preview
    const imageInputs = document.querySelectorAll('input[type="file"][accept*="image"]');
    
    imageInputs.forEach(input => {
        input.addEventListener('change', function() {
            if (this.files && this.files[0]) {
                const reader = new FileReader();
                
                reader.onload = function(e) {
                    const preview = document.createElement('div');
                    preview.className = 'image-preview';
                    preview.style.marginTop = '10px';
                    preview.style.maxWidth = '100%';
                    preview.style.borderRadius = '6px';
                    preview.style.overflow = 'hidden';
                    
                    const img = document.createElement('img');
                    img.src = e.target.result;
                    img.style.maxWidth = '100%';
                    
                    // Remove existing preview
                    const existingPreview = input.parentElement.querySelector('.image-preview');
                    if (existingPreview) {
                        existingPreview.remove();
                    }
                    
                    preview.appendChild(img);
                    input.parentElement.appendChild(preview);
                };
                
                reader.readAsDataURL(this.files[0]);
            }
        });
    });

    // Auto-dismiss alerts
    const alerts = document.querySelectorAll('.alert:not(.alert-permanent)');
    
    alerts.forEach(alert => {
        setTimeout(() => {
            alert.classList.add('fade-out');
            
            setTimeout(() => {
                alert.remove();
            }, 500);
        }, 5000);
    });
});