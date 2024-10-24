function popupIsOpen() {
  return (document.querySelector('#popup').style.display === 'block') ? true : false;
}

function renderPopupTab(title, link, content, id, active=false, openInNewTab=false) {
  const tabContent = document.createElement('div');
  tabContent.className = 'tab-pane fade ' + (active ? 'show active' : '');
  tabContent.id = 'tab-content-' + id;
  tabContent.setAttribute('role', 'tabpanel');
  tabContent.setAttribute('aria-labelledby', 'tab-button-' + id);
  tabContent.innerHTML = `
  <p>${content}</p>
  <div class="d-grid gap-2">
    <a href="${link}"${openInNewTab ? ' target="_blank"' : ''} class="btn btn-primary">Visa</a>
  </div>`;
  const contentContainer = document.querySelector('#popup-tab-content');
  contentContainer.appendChild(tabContent);

  const tabButton = document.createElement('li');
  tabButton.setAttribute('role', 'presentation');
  tabButton.className = 'nav-item';
  tabButton.innerHTML = `<button class="nav-link${active ? ' active' : ''}" id="tab-button-${id}" data-bs-toggle="pill" data-bs-target="#tab-content-${id}" type="button" role="tab" aria-controls="tab-content-${id}" ${active ? 'aria-selected="true"' : ''}>${title}</button>`;
  const tabButtonContainer = document.querySelector('#popup-tab-buttons');
  tabButtonContainer.appendChild(tabButton);
}

var openLamningInNewTab = false;
function renderPopup(header, description, id, link) {
  if (!header) return; // to deal with interactive editing layers

  var popup = document.querySelector('#popup');

  if (popupIsOpen()) {
    renderPopupTab(header, link, description, id, false, openLamningInNewTab);
  } else {
    document.querySelector('#popup-tab-buttons').innerHTML = '';
    document.querySelector('#popup-tab-content').innerHTML = '';
    renderPopupTab(header, link, description, id, true, openLamningInNewTab);
  }

  popup.style.display = 'block';
}

document.querySelector('#popup button').addEventListener('click', function() {
  document.querySelector('#popup').style.display = 'none';
});

function clearPopup() {
  document.querySelector('#popup-tab-buttons').innerHTML = '';
  document.querySelector('#popup-tab-content').innerHTML = '';
  popup.style.display = 'none';
}
