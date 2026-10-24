import { onAuthStateChanged, signOut } from 'firebase/auth';
import {
  collection,
  doc,
  getDoc,
  onSnapshot,
  serverTimestamp,
  setDoc,
} from 'firebase/firestore';
import { auth, db, firebaseConfigured, firebaseSetupMessage } from './firebase.js';

const $ = (selector, root = document) => root.querySelector(selector);
const listEl = $('#assignmentsList');
const peopleCountEl = $('#peopleCount');
const noticeEl = $('#pageNotice');
const setupNoticeEl = $('#setupNotice');
const editorPanel = $('#editorPanel');
const editorForm = $('#assignmentForm');
const sectionsEditor = $('#sectionsEditor');
const saveStatus = $('#saveStatus');
const signInNavBtn = $('#signInNavBtn');
const signOutBtn = $('#signOutBtn');
const editBtn = $('#editAssignmentsBtn');
const emptyAddBtn = $('#emptyAddBtn');
const searchInput = $('#peopleSearch');

let currentUser = null;
let allAssignments = [];
let currentUserAssignment = null;
let snapshotReady = false;

function setNotice(message = '', type = '') {
  noticeEl.textContent = message;
  noticeEl.className = `notice${type ? ` notice-${type}` : ''}`;
}

function safeUrl(value) {
  try {
    const url = new URL(value);
    return ['http:', 'https:'].includes(url.protocol) ? url.href : null;
  } catch {
    return null;
  }
}

function makeLink(link) {
  const url = safeUrl(String(link?.url || '').trim());
  if (!url) return null;
  const anchor = document.createElement('a');
  anchor.className = 'assignment-link';
  anchor.href = url;
  anchor.target = '_blank';
  anchor.rel = 'noopener noreferrer';
  const icon = document.createElement('span');
  icon.className = 'assignment-link-icon';
  icon.textContent = '↗';
  icon.setAttribute('aria-hidden', 'true');
  const label = document.createElement('span');
  label.className = 'assignment-link-label';
  label.textContent = String(link?.label || url);
  const urlText = document.createElement('span');
  urlText.className = 'assignment-link-url';
  urlText.textContent = url.replace(/^https?:\/\//, '');
  anchor.append(icon, label, urlText);
  return anchor;
}

function assignmentMatches(person, searchTerm) {
  if (!searchTerm) return true;
  const combined = [person.displayName, ...(person.sections || []).flatMap((section) => [
    section.title,
    ...(section.links || []).flatMap((link) => [link.label, link.url]),
  ])].join(' ').toLowerCase();
  return combined.includes(searchTerm);
}

function renderAssignments() {
  const searchTerm = searchInput.value.trim().toLowerCase();
  const visible = allAssignments
    .filter((person) => assignmentMatches(person, searchTerm))
    .sort((a, b) => String(a.displayName || '').localeCompare(String(b.displayName || '')));

  listEl.replaceChildren();
  peopleCountEl.textContent = String(allAssignments.length);

  for (const person of visible) {
    const details = document.createElement('details');
    details.className = 'person-card';
    if (currentUser && person.id === currentUser.uid) details.classList.add('person-card-own');

    const summary = document.createElement('summary');
    summary.className = 'person-summary';
    const avatar = document.createElement('span');
    avatar.className = 'person-avatar';
    avatar.textContent = String(person.displayName || '?').trim().charAt(0).toUpperCase() || '?';
    const identity = document.createElement('span');
    identity.className = 'person-identity';
    const name = document.createElement('span');
    name.className = 'person-name';
    name.textContent = person.displayName || 'Unnamed person';
    const subline = document.createElement('span');
    subline.className = 'person-subline';
    const sectionCount = (person.sections || []).length;
    const linkCount = (person.sections || []).reduce((sum, section) => sum + (Array.isArray(section.links) ? section.links.length : 0), 0);
    subline.textContent = `${sectionCount} section${sectionCount === 1 ? '' : 's'} · ${linkCount} link${linkCount === 1 ? '' : 's'}`;
    identity.append(name, subline);
    summary.append(avatar, identity);
    if (currentUser && person.id === currentUser.uid) {
      const ownerBadge = document.createElement('span');
      ownerBadge.className = 'owner-badge';
      ownerBadge.textContent = 'Your list';
      summary.append(ownerBadge);
    }
    const chevron = document.createElement('span');
    chevron.className = 'person-chevron';
    chevron.textContent = '⌄';
    chevron.setAttribute('aria-hidden', 'true');
    summary.append(chevron);
    details.append(summary);

    const body = document.createElement('div');
    body.className = 'person-details';
    const sections = Array.isArray(person.sections) ? person.sections : [];
    const hasLinks = sections.some((section) => Array.isArray(section.links) && section.links.some((link) => safeUrl(String(link.url || '').trim())));

    if (!sections.length || !hasLinks) {
      const empty = document.createElement('p');
      empty.className = 'person-empty';
      empty.textContent = 'No links shared here yet.';
      body.append(empty);
    }

    for (const section of sections) {
      const group = document.createElement('section');
      group.className = 'link-section';
      const heading = document.createElement('h3');
      heading.className = 'link-section-title';
      heading.textContent = section.title || 'Links';
      group.append(heading);
      const links = document.createElement('div');
      links.className = 'assignment-links';
      for (const item of Array.isArray(section.links) ? section.links : []) {
        const anchor = makeLink(item);
        if (anchor) links.append(anchor);
      }
      if (!links.childElementCount) {
        const noLinks = document.createElement('p');
        noLinks.className = 'section-empty';
        noLinks.textContent = 'No links in this section yet.';
        links.append(noLinks);
      }
      group.append(links);
      body.append(group);
    }
    details.append(body);
    listEl.append(details);
  }

  const showEmpty = snapshotReady && visible.length === 0;
  $('#emptyState').hidden = !showEmpty;
  if (snapshotReady && allAssignments.length === 0) {
    $('#emptyState h3').textContent = 'No assignments shared yet';
    $('#emptyState p').textContent = 'Be the first to add your name and useful links to the board.';
  } else if (showEmpty) {
    $('#emptyState h3').textContent = 'No matching people or links';
    $('#emptyState p').textContent = 'Try another search term.';
  }
}

function createLinkRow(link = {}) {
  const template = $('#linkRowTemplate');
  const fragment = template.content.cloneNode(true);
  const row = fragment.querySelector('.link-editor-row');
  row.querySelector('.link-label-input').value = link.label || '';
  row.querySelector('.link-url-input').value = link.url || '';
  row.querySelector('.remove-link-btn').addEventListener('click', () => row.remove());
  return fragment;
}

function createSectionCard(section = {}) {
  const card = document.createElement('div');
  card.className = 'section-editor-card';
  const header = document.createElement('div');
  header.className = 'section-editor-header';
  const titleLabel = document.createElement('label');
  titleLabel.className = 'field-label';
  titleLabel.textContent = 'Section name';
  const titleInput = document.createElement('input');
  titleInput.className = 'text-input section-title-input';
  titleInput.maxLength = 80;
  titleInput.required = true;
  titleInput.placeholder = 'e.g. Python assignments';
  titleInput.value = section.title || '';
  titleLabel.append(titleInput);
  const removeSectionBtn = document.createElement('button');
  removeSectionBtn.className = 'remove-button';
  removeSectionBtn.type = 'button';
  removeSectionBtn.textContent = 'Remove section';
  removeSectionBtn.addEventListener('click', () => card.remove());
  header.append(titleLabel, removeSectionBtn);
  const rows = document.createElement('div');
  rows.className = 'link-editor-list';
  for (const link of Array.isArray(section.links) ? section.links : []) rows.append(createLinkRow(link));
  if (!rows.childElementCount) rows.append(createLinkRow());
  const addLinkBtn = document.createElement('button');
  addLinkBtn.className = 'text-button add-link-btn';
  addLinkBtn.type = 'button';
  addLinkBtn.textContent = '+ Add a link';
  addLinkBtn.addEventListener('click', () => {
    if (rows.querySelectorAll('.link-editor-row').length >= 50) {
      saveStatus.textContent = 'A section can have up to 50 links.';
      return;
    }
    rows.append(createLinkRow());
    saveStatus.textContent = '';
  });
  card.append(header, rows, addLinkBtn);
  return card;
}

function renderEditorSections(sections) {
  sectionsEditor.replaceChildren();
  const initial = Array.isArray(sections) && sections.length ? sections : [{ title: 'Assignments', links: [] }];
  initial.forEach((section) => sectionsEditor.append(createSectionCard(section)));
}

function collectEditorSections() {
  const cards = [...sectionsEditor.querySelectorAll('.section-editor-card')];
  if (cards.length > 30) throw new Error('Please keep your list to 30 sections or fewer.');
  const result = [];
  for (const [index, card] of cards.entries()) {
    const title = card.querySelector('.section-title-input').value.trim();
    if (!title) throw new Error(`Enter a name for section ${index + 1}.`);
    const links = [];
    const rows = [...card.querySelectorAll('.link-editor-row')];
    if (rows.length > 50) throw new Error(`Section “${title}” has more than 50 links.`);
    for (const [rowIndex, row] of rows.entries()) {
      const label = row.querySelector('.link-label-input').value.trim();
      const rawUrl = row.querySelector('.link-url-input').value.trim();
      if (!label && !rawUrl) continue;
      if (!label) throw new Error(`Add a display name for link ${rowIndex + 1} in “${title}”.`);
      const url = safeUrl(rawUrl);
      if (!url) throw new Error(`Enter a valid http:// or https:// URL for “${label}”.`);
      links.push({ label, url });
    }
    result.push({ title, links });
  }
  if (result.length === 0) throw new Error('Add at least one section.');
  return result;
}

async function openEditor() {
  if (!currentUser) {
    window.location.href = '/login.html?next=edit';
    return;
  }
  saveStatus.textContent = '';
  $('#displayName').value = currentUserAssignment?.displayName || currentUser.displayName || '';
  renderEditorSections(currentUserAssignment?.sections || [{ title: 'Assignments', links: [] }]);
  editorPanel.hidden = false;
  editorPanel.scrollIntoView({ behavior: 'smooth', block: 'start' });
  $('#displayName').focus({ preventScroll: true });
}

editBtn.addEventListener('click', openEditor);
emptyAddBtn.addEventListener('click', openEditor);
$('#closeEditorBtn').addEventListener('click', () => { editorPanel.hidden = true; });
$('#addSectionBtn').addEventListener('click', () => {
  if (sectionsEditor.querySelectorAll('.section-editor-card').length >= 30) {
    saveStatus.textContent = 'You can add up to 30 sections.';
    return;
  }
  sectionsEditor.append(createSectionCard({ title: '', links: [] }));
  saveStatus.textContent = '';
});
searchInput.addEventListener('input', renderAssignments);

editorForm.addEventListener('submit', async (event) => {
  event.preventDefault();
  if (!currentUser) {
    window.location.href = '/login.html?next=edit';
    return;
  }
  const displayName = $('#displayName').value.trim();
  if (!displayName) {
    saveStatus.textContent = 'Please enter your name.';
    return;
  }
  if (displayName.length > 80) {
    saveStatus.textContent = 'Your name must be 80 characters or fewer.';
    return;
  }

  let sections;
  try {
    sections = collectEditorSections();
  } catch (error) {
    saveStatus.textContent = error.message;
    return;
  }

  const saveBtn = $('#saveAssignmentsBtn');
  saveBtn.disabled = true;
  saveBtn.textContent = 'Saving…';
  saveStatus.textContent = '';
  try {
    await setDoc(doc(db, 'assignments', currentUser.uid), {
      displayName,
      sections,
      updatedAt: serverTimestamp(),
    });
    currentUserAssignment = { id: currentUser.uid, displayName, sections };
    saveStatus.textContent = 'Saved successfully.';
    saveStatus.className = 'form-hint notice-success';
    setNotice('Your assignment links have been updated.', 'success');
  } catch (error) {
    console.error('Could not save assignments:', error);
    saveStatus.textContent = error.code === 'permission-denied'
      ? 'Permission denied. Check that firestore.rules has been published in Firebase.'
      : 'Could not save your changes. Check your connection and Firebase settings.';
    saveStatus.className = 'form-hint notice-error';
  } finally {
    saveBtn.disabled = false;
    saveBtn.textContent = 'Save changes';
  }
});

signOutBtn.addEventListener('click', async () => {
  try {
    await signOut(auth);
    editorPanel.hidden = true;
    setNotice('You have signed out.', 'success');
  } catch (error) {
    console.error(error);
    setNotice('Could not sign out. Please try again.', 'error');
  }
});

if (!firebaseConfigured) {
  setupNoticeEl.hidden = false;
  setupNoticeEl.textContent = firebaseSetupMessage();
  editBtn.disabled = true;
  emptyAddBtn.disabled = true;
  listEl.innerHTML = '';
  snapshotReady = false;
  setNotice('Connect your Firebase project to load the live assignment board.', 'error');
} else {
  onAuthStateChanged(auth, async (user) => {
    currentUser = user;
    signInNavBtn.hidden = Boolean(user);
    signOutBtn.hidden = !user;
    editBtn.disabled = false;
    editBtn.innerHTML = user ? '<span aria-hidden="true">✎</span> Add / edit my links' : '<span aria-hidden="true">↗</span> Login to add links';
    editBtn.title = user ? 'Edit the links shared by your account' : 'Sign in to add your assignment links';
    if (user) {
      try {
        const ownDoc = await getDoc(doc(db, 'assignments', user.uid));
        currentUserAssignment = ownDoc.exists() ? { id: ownDoc.id, ...ownDoc.data() } : null;
      } catch (error) {
        console.error('Could not load your assignment profile:', error);
      }
      if (new URLSearchParams(window.location.search).get('edit') === '1' || new URLSearchParams(window.location.search).get('edit') === 'true') {
        await openEditor();
      }
    } else {
      currentUserAssignment = null;
      editorPanel.hidden = true;
    }
    renderAssignments();
  });

  onSnapshot(collection(db, 'assignments'), (snapshot) => {
    allAssignments = snapshot.docs.map((item) => ({ id: item.id, ...item.data() }));
    snapshotReady = true;
    currentUserAssignment = currentUser ? allAssignments.find((item) => item.id === currentUser.uid) || currentUserAssignment : null;
    renderAssignments();
    setNotice(allAssignments.length ? `${allAssignments.length} ${allAssignments.length === 1 ? 'person has' : 'people have'} shared their links.` : 'No profiles yet — add yours to get started.', '');
  }, (error) => {
    console.error('Could not load assignment board:', error);
    snapshotReady = true;
    setNotice('Could not load assignments. Confirm that Firestore is enabled and the rules are published.', 'error');
    renderAssignments();
  });
}
