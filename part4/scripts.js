const API_BASE_URL = 'http://127.0.0.1:5000/api/v1';

document.addEventListener('DOMContentLoaded', () => {
  const loginForm = document.getElementById('login-form');
  if (loginForm) {
    loginForm.addEventListener('submit', async (event) => {
      event.preventDefault();
      const email = document.getElementById('email').value;
      const password = document.getElementById('password').value;
      await loginUser(email, password);
    });
  }

  const token = checkAuthentication();

  const reviewForm = document.getElementById('review-form');
  if (reviewForm) {
    const placeId = getPlaceIdFromURL();
    fillPlaceName(placeId);
    reviewForm.addEventListener('submit', async (event) => {
      event.preventDefault();
      const reviewText = document.getElementById('review').value;
      const rating = document.getElementById('rating').value;
      const response = await submitReview(token, placeId, reviewText, rating);
      handleResponse(response);
    });
  }

  const placesList = document.getElementById('places-list');
  if (placesList) {
    document.getElementById('price-filter').addEventListener('change', (event) => {
      const selectedPrice = event.target.value;
      document.querySelectorAll('.place-card').forEach((card) => {
        const price = parseFloat(card.dataset.price);
        if (selectedPrice === 'all' || price <= parseFloat(selectedPrice)) {
          card.style.display = 'block';
        } else {
          card.style.display = 'none';
        }
      });
    });
  }
});

async function loginUser (email, password) {
  const response = await fetch(`${API_BASE_URL}/auth/login`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ email, password })
  });

  if (response.ok) {
    const data = await response.json();
    document.cookie = `token=${data.access_token}; path=/`;
    window.location.href = 'index.html';
  } else {
    window.alert('Login failed: ' + response.statusText);
  }
}

function getCookie (name) {
  const cookies = document.cookie.split(';');
  for (const cookie of cookies) {
    const [key, value] = cookie.trim().split('=');
    if (key === name) {
      return value;
    }
  }
  return null;
}

function checkAuthentication () {
  const token = getCookie('token');
  const loginLink = document.getElementById('login-link');
  const addReviewSection = document.getElementById('add-review');

  if (!token && document.getElementById('review-form')) {
    window.location.href = 'index.html';
    return token;
  }

  if (loginLink) {
    if (!token) {
      loginLink.style.display = 'block';
    } else {
      loginLink.style.display = 'none';
    }
  }

  if (addReviewSection) {
    if (!token) {
      addReviewSection.style.display = 'none';
    } else {
      addReviewSection.style.display = 'block';
    }
  }

  if (token && document.getElementById('places-list')) {
    fetchPlaces(token);
  }

  if (document.getElementById('place-details')) {
    const placeId = getPlaceIdFromURL();
    const addReviewLink = document.querySelector('#add-review a');
    if (addReviewLink) {
      addReviewLink.href = `add_review.html?id=${placeId}`;
    }
    fetchPlaceDetails(token, placeId);
  }

  return token;
}

function getPlaceIdFromURL () {
  const params = new URLSearchParams(window.location.search);
  return params.get('id');
}

async function fetchPlaces (token) {
  const response = await fetch(`${API_BASE_URL}/places/`, {
    method: 'GET',
    headers: {
      Authorization: `Bearer ${token}`
    }
  });

  if (response.ok) {
    const places = await response.json();
    displayPlaces(places);
  }
}

function displayPlaces (places) {
  const placesList = document.getElementById('places-list');
  placesList.innerHTML = '';
  places.forEach((place) => {
    const card = document.createElement('div');
    card.className = 'place-card';
    card.dataset.price = place.price;
    card.innerHTML = `
      <h2>${place.title}</h2>
      <p>Price per night: $${place.price}</p>
      <a href="place.html?id=${place.id}" class="details-button">View Details</a>
    `;
    placesList.appendChild(card);
  });
}

async function fetchPlaceDetails (token, placeId) {
  const headers = {};
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }
  const response = await fetch(`${API_BASE_URL}/places/${placeId}`, {
    method: 'GET',
    headers
  });

  if (response.ok) {
    const place = await response.json();
    displayPlaceDetails(place);
  }
}

function displayPlaceDetails (place) {
  const placeDetails = document.getElementById('place-details');
  placeDetails.innerHTML = '';

  const title = document.createElement('h1');
  title.textContent = place.title;
  placeDetails.appendChild(title);

  const info = document.createElement('div');
  info.className = 'place-info';
  const host = `${place.owner.first_name} ${place.owner.last_name}`;
  const amenities = place.amenities.map((amenity) => amenity.name).join(', ');
  info.innerHTML = `
    <p><strong>Host:</strong> ${host}</p>
    <p><strong>Price per night:</strong> $${place.price}</p>
    <p><strong>Description:</strong> ${place.description}</p>
    <p><strong>Amenities:</strong> ${amenities}</p>
  `;
  placeDetails.appendChild(info);

  displayReviews(place.reviews);
}

function displayReviews (reviews) {
  const reviewsSection = document.getElementById('reviews');
  reviewsSection.querySelectorAll('.review-card').forEach((card) => card.remove());
  reviews.forEach(async (review) => {
    const card = document.createElement('div');
    card.className = 'review-card';
    const stars = '★'.repeat(review.rating) + '☆'.repeat(5 - review.rating);
    card.innerHTML = `
      <p><strong>${review.user_id}:</strong></p>
      <p>${review.text}</p>
      <p>Rating: ${stars}</p>
    `;
    reviewsSection.appendChild(card);
    const userName = await fetchUserName(review.user_id);
    card.querySelector('strong').textContent = `${userName}:`;
  });
}

async function fetchUserName (userId) {
  const response = await fetch(`${API_BASE_URL}/users/${userId}`);
  if (response.ok) {
    const user = await response.json();
    return `${user.first_name} ${user.last_name}`;
  }
  return userId;
}

async function fillPlaceName (placeId) {
  const response = await fetch(`${API_BASE_URL}/places/${placeId}`);
  if (response.ok) {
    const place = await response.json();
    document.getElementById('place-name').textContent = `Reviewing: ${place.title}`;
  }
}

async function submitReview (token, placeId, reviewText, rating) {
  const response = await fetch(`${API_BASE_URL}/reviews/`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`
    },
    body: JSON.stringify({
      text: reviewText,
      rating: parseInt(rating, 10),
      place_id: placeId
    })
  });
  return response;
}

function handleResponse (response) {
  if (response.ok) {
    window.alert('Review submitted successfully!');
    document.getElementById('review-form').reset();
  } else {
    window.alert('Failed to submit review');
  }
}
