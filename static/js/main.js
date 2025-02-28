/**
 * MindTrack - Main JavaScript
 * Provides interactivity for the MindTrack landing page
 */

document.addEventListener('DOMContentLoaded', function() {
    // ======= Mobile Menu Toggle =======
    const mobileMenuButton = document.querySelector('.mobile-menu-toggle');
    const navLinks = document.querySelector('.nav-links');
    const authButtons = document.querySelector('.auth-buttons');
    
    if (mobileMenuButton) {
        mobileMenuButton.addEventListener('click', function() {
            navLinks.classList.toggle('mobile-active');
            authButtons.classList.toggle('mobile-active');
            
            // Animate hamburger to X
            const spans = this.querySelectorAll('span');
            if (spans.length >= 3) {
                spans[0].style.transform = spans[0].style.transform === 'rotate(45deg) translate(5px, 5px)' ? '' : 'rotate(45deg) translate(5px, 5px)';
                spans[1].style.opacity = spans[1].style.opacity === '0' ? '1' : '0';
                spans[2].style.transform = spans[2].style.transform === 'rotate(-45deg) translate(7px, -6px)' ? '' : 'rotate(-45deg) translate(7px, -6px)';
            }
        });
    }

    // ======= Smooth Scrolling for Anchor Links =======
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function(e) {
            e.preventDefault();
            
            const targetId = this.getAttribute('href');
            if (targetId === '#') return;
            
            const targetElement = document.querySelector(targetId);
            if (targetElement) {
                targetElement.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
                
                // Close mobile menu if open
                if (navLinks && navLinks.classList.contains('mobile-active')) {
                    navLinks.classList.remove('mobile-active');
                    authButtons.classList.remove('mobile-active');
                    
                    const spans = mobileMenuButton.querySelectorAll('span');
                    if (spans.length >= 3) {
                        spans[0].style.transform = '';
                        spans[1].style.opacity = '1';
                        spans[2].style.transform = '';
                    }
                }
            }
        });
    });
    
    // ======= Testimonial Slider =======
    const testimonialSlider = document.querySelector('.testimonial-slider');
    if (testimonialSlider) {
        const testimonials = testimonialSlider.querySelectorAll('.testimonial');
        
        if (testimonials.length > 1) {
            // Create slider navigation
            const sliderNavigation = document.createElement('div');
            sliderNavigation.className = 'slider-navigation';
            sliderNavigation.innerHTML = `
                <button class="btn btn-circle slider-prev" aria-label="Previous testimonial">
                    <i class="fas fa-chevron-left"></i>
                </button>
                <div class="slider-dots"></div>
                <button class="btn btn-circle slider-next" aria-label="Next testimonial">
                    <i class="fas fa-chevron-right"></i>
                </button>
            `;
            
            // Append navigation after the slider
            testimonialSlider.parentNode.insertBefore(sliderNavigation, testimonialSlider.nextSibling);
            
            // Create dots for each testimonial
            const dotsContainer = sliderNavigation.querySelector('.slider-dots');
            let currentSlide = 0;
            
            testimonials.forEach((_, index) => {
                const dot = document.createElement('button');
                dot.className = 'slider-dot' + (index === 0 ? ' active' : '');
                dot.setAttribute('aria-label', `Go to testimonial ${index + 1}`);
                
                dot.addEventListener('click', () => {
                    scrollToSlide(index);
                });
                
                dotsContainer.appendChild(dot);
            });
            
            // Handle navigation buttons
            const prevBtn = sliderNavigation.querySelector('.slider-prev');
            const nextBtn = sliderNavigation.querySelector('.slider-next');
            
            prevBtn.addEventListener('click', () => {
                if (currentSlide > 0) {
                    scrollToSlide(currentSlide - 1);
                } else {
                    scrollToSlide(testimonials.length - 1); // loop to the end
                }
            });
            
            nextBtn.addEventListener('click', () => {
                if (currentSlide < testimonials.length - 1) {
                    scrollToSlide(currentSlide + 1);
                } else {
                    scrollToSlide(0); // loop to the beginning
                }
            });
            
            // Function to scroll to a specific slide
            function scrollToSlide(index) {
                const targetSlide = testimonials[index];
                const dots = dotsContainer.querySelectorAll('.slider-dot');
                
                // Update active state
                dots.forEach((dot, i) => {
                    dot.classList.toggle('active', i === index);
                });
                
                // Scroll to the slide
                if (targetSlide) {
                    const slideWidth = targetSlide.offsetWidth;
                    const slideMargin = parseInt(window.getComputedStyle(targetSlide).marginRight);
                    const scrollPosition = index * (slideWidth + slideMargin);
                    
                    testimonialSlider.scrollTo({
                        left: scrollPosition,
                        behavior: 'smooth'
                    });
                    
                    currentSlide = index;
                }
            }
            
            // Update dots when user manually scrolls
            testimonialSlider.addEventListener('scroll', () => {
                // Debounce the scroll event for performance
                clearTimeout(testimonialSlider.scrollTimer);
                testimonialSlider.scrollTimer = setTimeout(() => {
                    // Calculate which slide is most visible
                    const slideWidth = testimonials[0].offsetWidth;
                    const slideMargin = parseInt(window.getComputedStyle(testimonials[0]).marginRight);
                    const scrollPosition = testimonialSlider.scrollLeft;
                    const visibleSlideIndex = Math.round(scrollPosition / (slideWidth + slideMargin));
                    
                    // Update dots if needed
                    if (visibleSlideIndex !== currentSlide) {
                        const dots = dotsContainer.querySelectorAll('.slider-dot');
                        dots.forEach((dot, i) => {
                            dot.classList.toggle('active', i === visibleSlideIndex);
                        });
                        currentSlide = visibleSlideIndex;
                    }
                }, 100);
            });
        }
    }
    
    // ======= Animate on scroll elements =======
    const animatedElements = document.querySelectorAll('.benefit-card, .step-card, .cta-card');
    
    if ('IntersectionObserver' in window) {
        const animationObserver = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('animated');
                    animationObserver.unobserve(entry.target); // Stop observing once animation is triggered
                }
            });
        }, { threshold: 0.2 });
        
        animatedElements.forEach(element => {
            // Add initial state class
            element.classList.add('fade-in-element');
            animationObserver.observe(element);
        });
    } else {
        // Fallback for browsers that don't support IntersectionObserver
        animatedElements.forEach(element => {
            element.classList.add('animated');
        });
    }
    
    // ======= User menu functionality =======
    const userIcon = document.querySelector('.user-icon');
    const userMenu = document.querySelector('.user-menu');
    
    if (userIcon && userMenu) {
        userIcon.addEventListener('click', function(e) {
            e.stopPropagation();
            userMenu.classList.toggle('show');
        });
        
        // Close menu when clicking outside
        document.addEventListener('click', function() {
            if (userMenu.classList.contains('show')) {
                userMenu.classList.remove('show');
            }
        });
        
        // Prevent menu from closing when clicking inside it
        userMenu.addEventListener('click', function(e) {
            e.stopPropagation();
        });
    }
    
    // ======= Form validation for CTA =======
    /*
    const ctaForm = document.querySelector('.cta-form');
    if (ctaForm) {
        ctaForm.addEventListener('submit', function(e) {
            let isValid = true;
            const emailInput = this.querySelector('input[type="email"]');
            
            if (emailInput) {
                const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
                if (!emailPattern.test(emailInput.value)) {
                    isValid = false;
                    emailInput.classList.add('error');
                    
                    // Create or update error message
                    let errorMessage = emailInput.parentNode.querySelector('.error-message');
                    if (!errorMessage) {
                        errorMessage = document.createElement('div');
                        errorMessage.className = 'error-message';
                        emailInput.parentNode.appendChild(errorMessage);
                    }
                    errorMessage.textContent = 'Please enter a valid email address';
                } else {
                    emailInput.classList.remove('error');
                    const errorMessage = emailInput.parentNode.querySelector('.error-message');
                    if (errorMessage) {
                        errorMessage.remove();
                    }
                }
            }
            
            if (!isValid) {
                e.preventDefault();
            }
        });
    }
    */
    

    // ======= Add animation classes =======
    // Add these CSS classes to the stylesheet for animated elements
    const style = document.createElement('style');
    style.innerHTML = `
        .fade-in-element {
            opacity: 0;
            transform: translateY(20px);
            transition: opacity 0.6s ease-out, transform 0.6s ease-out;
        }
        
        .fade-in-element.animated {
            opacity: 1;
            transform: translateY(0);
        }
        
        .btn-circle {
            width: 40px;
            height: 40px;
            border-radius: 50%;
            padding: 0;
            display: flex;
            align-items: center;
            justify-content: center;
            background-color: var(--bg-light);
            border: 1px solid var(--border-color);
            color: var(--text-dark);
            box-shadow: var(--shadow-sm);
            transition: all var(--transition-normal);
        }
        
        .btn-circle:hover {
            background-color: var(--primary-light);
            color: var(--primary-dark);
            box-shadow: var(--shadow-md);
        }
        
        .slider-navigation {
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 1rem;
            margin-top: 1.5rem;
        }
        
        .slider-dots {
            display: flex;
            gap: 0.5rem;
        }
        
        .slider-dot {
            width: 10px;
            height: 10px;
            border-radius: 50%;
            background-color: var(--border-color);
            border: none;
            padding: 0;
            cursor: pointer;
            transition: all var(--transition-normal);
        }
        
        .slider-dot.active {
            background-color: var(--primary-color);
            transform: scale(1.2);
        }
        
        .error-message {
            color: var(--dark-red);
            font-size: var(--font-size-sm);
            margin-top: 4px;
        }
        
        input.error {
            border-color: var(--dark-red);
        }
    `;
    document.head.appendChild(style);
});
