document.addEventListener('DOMContentLoaded', () => {
    // 1. Check authentication status on page load
    checkAuthentication();

    // 2. Handle Login Form Submission
    const loginForm = document.getElementById('login-form');
    if (loginForm) {
        loginForm.addEventListener('submit', async (event) => {
            event.preventDefault();
            const email = document.getElementById('email').value;
            const password = document.getElementById('password').value;
            await loginUser(email, password);
        });
    }

    // 3. Handle Price Filter
    const priceFilter = document.getElementById('price-filter');
    if (priceFilter) {
        priceFilter.addEventListener('change', (event) => {
            const selectedPrice = event.target.value;
            const placeCards = document.querySelectorAll('.place-card');

            placeCards.forEach(card => {
                const cardPrice = parseFloat(card.getAttribute('data-price'));
                
                if (selectedPrice === 'All') {
                    card.style.display = 'block';
                } else {
                    if (cardPrice <= parseFloat(selectedPrice)) {
                        card.style.display = 'block';
                    } else {
                        card.style.display = 'none';
                    }
                }
            });
        });
    }

    // 4. Handle Add Review Form Submission
    const reviewForm = document.getElementById('review-form');
    if (reviewForm) {
        const token = getCookie('token');
        if (!token) {
            window.location.href = 'index.html';
        } else {
            reviewForm.addEventListener('submit', async (event) => {
                event.preventDefault();
                const comment = document.getElementById('comment').value;
                const rating = document.getElementById('rating').value;
                const placeId = getPlaceIdFromURL();
                
                if (placeId) {
                    await submitReview(token, placeId, comment, rating);
                } else {
                    alert('Error: Place ID is missing.');
                }
            });
        }
    }
});

// ==========================================
// CORE FUNCTIONS
// ==========================================

// Function to get a cookie value by its name
function getCookie(name) {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) return parts.pop().split(';').shift();
    return null;
}

// Function to check if user is authenticated and control UI
function checkAuthentication() {
    const token = getCookie('token');
    const loginLink = document.getElementById('login-link');
    const addReviewSection = document.getElementById('add-review');
    const reviewForm = document.getElementById('review-form');
    const placeId = getPlaceIdFromURL();

    // Redirect unauthenticated users away from the review page
    if (reviewForm && !token) {
        window.location.href = 'index.html';
        return;
    }

    // Control Login Link Visibility
    if (loginLink) {
        loginLink.style.display = !token ? 'block' : 'none';
    }

    // Control Add Review Button Visibility & URL
    if (addReviewSection) {
        addReviewSection.style.display = !token ? 'none' : 'block';
        if (placeId) {
            const reviewLink = addReviewSection.querySelector('a');
            if (reviewLink) {
                reviewLink.href = `add_review.html?id=${placeId}`;
            }
        }
    }
    
    // Fetch places for Index Page
    const placesList = document.getElementById('places-list');
    if (placesList) {
        fetchPlaces(token);
    }

    // Fetch details for Place Details Page
    const placeDetails = document.getElementById('place-details');
    if (placeDetails) {
        if (placeId) {
            fetchPlaceDetails(token, placeId);
        }
    }
}

// Function to extract Place ID from URL
function getPlaceIdFromURL() {
    const urlParams = new URLSearchParams(window.location.search);
    return urlParams.get('id');
}

// ==========================================
// API REQUEST FUNCTIONS
// ==========================================

// Authenticate User
async function loginUser(email, password) {
    try {
        const response = await fetch('http://127.0.0.1:5000/api/v1/auth/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, password })
        });

        if (response.ok) {
            const data = await response.json();
            document.cookie = `token=${data.access_token}; path=/`;
            window.location.href = 'index.html';
        } else {
            alert('Login failed: Invalid email or password');
        }
    } catch (error) {
        console.error('Error logging in:', error);
        alert('An error occurred while logging in.');
    }
}

// Fetch Places List
async function fetchPlaces(token) {
    try {
        const headers = { 'Content-Type': 'application/json' };
        if (token) headers['Authorization'] = `Bearer ${token}`;

        const response = await fetch('http://127.0.0.1:5000/api/v1/places', {
            method: 'GET',
            headers: headers
        });

        if (response.ok) {
            const places = await response.json();
            displayPlaces(places);
        } else {
            console.error('Failed to fetch places');
        }
    } catch (error) {
        console.error('Error fetching places:', error);
    }
}

// Fetch Place Details
async function fetchPlaceDetails(token, placeId) {
    try {
        const headers = { 'Content-Type': 'application/json' };
        if (token) headers['Authorization'] = `Bearer ${token}`;

        const response = await fetch(`http://127.0.0.1:5000/api/v1/places/${placeId}`, {
            method: 'GET',
            headers: headers
        });

        if (response.ok) {
            const place = await response.json();
            displayPlaceDetails(place);
        } else {
            console.error('Failed to fetch place details');
            alert('Place not found!');
        }
    } catch (error) {
        console.error('Error fetching place details:', error);
    }
}

// Submit Review
async function submitReview(token, placeId, text, rating) {
    try {
        const response = await fetch(`http://127.0.0.1:5000/api/v1/places/${placeId}/reviews`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({
                text: text,
                rating: parseInt(rating),
                user_id: "replace_with_actual_user_id" // Needs to be handled correctly in backend
            })
        });

        if (response.ok) {
            alert('Review submitted successfully!');
            window.location.href = `place.html?id=${placeId}`;
        } else {
            const errData = await response.json();
            alert(`Failed to submit review: ${errData.message || response.statusText}`);
        }
    } catch (error) {
        console.error('Error submitting review:', error);
        alert('An error occurred while submitting your review.');
    }
}

// ==========================================
// DOM MANIPULATION FUNCTIONS
// ==========================================

// Populate places list in Index
function displayPlaces(places) {
    const placesList = document.getElementById('places-list');
    if (!placesList) return;

    placesList.innerHTML = ''; 

    places.forEach(place => {
        const placeCard = document.createElement('article');
        placeCard.className = 'place-card';
        
        const price = place.price || 0;
        placeCard.setAttribute('data-price', price);

        const title = place.title || place.name || 'Unnamed Place';

        placeCard.innerHTML = `
            <h2>${title}</h2>
            <p>Price: $${price} per night</p>
            <a href="place.html?id=${place.id}" class="details-button">View Details</a>
        `;

        placesList.appendChild(placeCard);
    });
}

// Populate details in Place page
function displayPlaceDetails(place) {
    const placeDetailsContainer = document.getElementById('place-details');
    if (!placeDetailsContainer) return;

    const placeInfo = placeDetailsContainer.querySelector('.place-info');
    if (placeInfo) {
        const title = place.title || place.name || 'Unnamed Place';
        const host = place.owner ? (place.owner.first_name + ' ' + place.owner.last_name) : 'Anonymous Host';
        const amenitiesList = place.amenities && place.amenities.length > 0 
            ? place.amenities.map(a => a.name).join(', ') 
            : 'No amenities listed';

        // Custom Icons Section
        const featuresHtml = `
            <div style="display: flex; gap: 20px; margin: 15px 0; align-items: center;">
                <span style="display: flex; align-items: center; gap: 8px;">
                    <img src="image/icon_bed.png" alt="Bed" style="width: 24px; height: 24px;">
                    ${place.number_rooms || 2} Rooms
                </span>
                <span style="display: flex; align-items: center; gap: 8px;">
                    <img src="image/icon_bath.png" alt="Bath" style="width: 24px; height: 24px;">
                    ${place.number_bathrooms || 1} Baths
                </span>
                <span style="display: flex; align-items: center; gap: 8px;">
                    <img src="image/icon_wifi.png" alt="WiFi" style="width: 24px; height: 24px;">
                    WiFi included
                </span>
            </div>
        `;

        placeInfo.innerHTML = `
            <h1>${title}</h1>
            <p><strong>Host:</strong> ${host}</p>
            <p><strong>Price:</strong> $${place.price || 0} per night</p>
            ${featuresHtml}
            <p><strong>Description:</strong> ${place.description || 'No description provided.'}</p>
            <p><strong>Amenities:</strong> ${amenitiesList}</p>
        `;
    }

    const reviewsContainer = placeDetailsContainer.querySelector('.reviews');
    if (reviewsContainer) {
        reviewsContainer.innerHTML = '<h2>Reviews</h2>'; 
        
        if (place.reviews && place.reviews.length > 0) {
            place.reviews.forEach(review => {
                const userName = review.user ? (review.user.first_name + ' ' + review.user.last_name) : 'Anonymous';
                reviewsContainer.innerHTML += `
                    <article class="review-card">
                        <p><strong>User:</strong> ${userName}</p>
                        <p><strong>Rating:</strong> ${review.rating}/5</p>
                        <p><strong>Comment:</strong> ${review.text}</p>
                    </article>
                `;
            });
        } else {
            reviewsContainer.innerHTML += `<p>No reviews yet. Be the first to review!</p>`;
        }
    }
}