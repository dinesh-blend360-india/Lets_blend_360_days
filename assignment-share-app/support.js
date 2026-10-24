import { onAuthStateChanged } from 'firebase/auth';
import { addDoc, collection, serverTimestamp } from 'firebase/firestore';
import { auth, db, firebaseConfigured, firebaseSetupMessage } from './firebase.js';

const $ = (selector) => document.querySelector(selector);
const form = $('#supportForm');
const notice = $('#supportNotice');
const setupNotice = $('#setupNotice');
const submitButton = $('#sendTicketBtn');
let signedInUser = null;

function setNotice(message = '', type = '') {
  notice.textContent = message;
  notice.className = `notice${type ? ` notice-${type}` : ''}`;
}

if (!firebaseConfigured) {
  setupNotice.hidden = false;
  setupNotice.textContent = firebaseSetupMessage();
  submitButton.disabled = true;
} else {
  onAuthStateChanged(auth, (user) => {
    signedInUser = user;
    const loginBtn = $('#supportLoginBtn');
    if (user) {
      loginBtn.textContent = 'Assignments';
      loginBtn.href = '/index.html';
      if (!$('#supportName').value.trim()) $('#supportName').value = user.displayName || '';
      if (!$('#supportEmail').value.trim()) $('#supportEmail').value = user.email || '';
    }
  });
}

form.addEventListener('submit', async (event) => {
  event.preventDefault();
  if (!firebaseConfigured) return setNotice(firebaseSetupMessage(), 'error');
  const name = $('#supportName').value.trim();
  const email = $('#supportEmail').value.trim();
  const message = $('#supportMessage').value.trim();
  if (!name || !email || !message) return setNotice('Please complete all fields.', 'error');
  if (message.length > 5000) return setNotice('Your message must be 5,000 characters or fewer.', 'error');

  submitButton.disabled = true;
  submitButton.textContent = 'Submitting…';
  setNotice('');
  try {
    await addDoc(collection(db, 'supportTickets'), {
      name,
      email,
      message,
      createdAt: serverTimestamp(),
    });
    form.reset();
    if (signedInUser) {
      $('#supportName').value = signedInUser.displayName || '';
      $('#supportEmail').value = signedInUser.email || '';
    }
    setNotice('Your support ticket was submitted. Thank you!', 'success');
  } catch (error) {
    console.error('Could not submit support ticket:', error);
    setNotice(error.code === 'permission-denied'
      ? 'Firebase rejected this ticket. Make sure the provided firestore.rules have been published.'
      : 'Could not send your ticket. Check the connection and try again.', 'error');
  } finally {
    submitButton.disabled = false;
    submitButton.innerHTML = 'Submit support ticket <span aria-hidden="true">→</span>';
  }
});
