// Main JavaScript for Student Portfolio Platform

document.addEventListener('DOMContentLoaded', function() {
  // Initialize tooltips
  const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
  tooltipTriggerList.map(function(tooltipTriggerEl) {
    return new bootstrap.Tooltip(tooltipTriggerEl);
  });

  // GitHub repository search
  const repoSearchInput = document.getElementById('repo-search');
  if (repoSearchInput) {
    repoSearchInput.addEventListener('keyup', function() {
      const searchTerm = this.value.toLowerCase();
      const repoItems = document.querySelectorAll('.repo-item');
      
      repoItems.forEach(item => {
        const repoName = item.querySelector('.repo-name').textContent.toLowerCase();
        const repoDesc = item.querySelector('.repo-description').textContent.toLowerCase();
        
        if (repoName.includes(searchTerm) || repoDesc.includes(searchTerm)) {
          item.style.display = 'block';
        } else {
          item.style.display = 'none';
        }
      });
    });
  }

  // Show loading spinner for GitHub import
  const importForm = document.getElementById('import-github-form');
  if (importForm) {
    importForm.addEventListener('submit', function() {
      const spinner = document.createElement('div');
      spinner.className = 'spinner-overlay';
      spinner.innerHTML = `
        <div class="spinner-border text-light" role="status" style="width: 3rem; height: 3rem;">
          <span class="visually-hidden">Loading...</span>
        </div>
      `;
      document.body.appendChild(spinner);
    });
  }

  // Toggle repositories selection
  const selectAllBtn = document.getElementById('select-all-repos');
  if (selectAllBtn) {
    selectAllBtn.addEventListener('click', function() {
      const checkboxes = document.querySelectorAll('.repo-checkbox');
      checkboxes.forEach(checkbox => {
        checkbox.checked = true;
      });
    });
  }

  const unselectAllBtn = document.getElementById('unselect-all-repos');
  if (unselectAllBtn) {
    unselectAllBtn.addEventListener('click', function() {
      const checkboxes = document.querySelectorAll('.repo-checkbox');
      checkboxes.forEach(checkbox => {
        checkbox.checked = false;
      });
    });
  }

  // Check for notifications periodically
  function checkNotifications() {
    if (!document.getElementById('notification-badge')) return;
    
    fetch('/check_notifications')
      .then(response => response.json())
      .then(data => {
        const badge = document.getElementById('notification-badge');
        if (data.unread_count > 0) {
          badge.textContent = data.unread_count;
          badge.classList.remove('d-none');
        } else {
          badge.classList.add('d-none');
        }
      })
      .catch(error => console.error('Error checking notifications:', error));
  }

  // Check notifications every 30 seconds if user is logged in
  if (document.getElementById('notification-badge')) {
    checkNotifications();
    setInterval(checkNotifications, 30000);
  }

  // Password strength indicator
  const passwordInput = document.getElementById('password');
  const strengthIndicator = document.getElementById('password-strength');
  
  if (passwordInput && strengthIndicator) {
    passwordInput.addEventListener('input', function() {
      const password = this.value;
      let strength = 0;
      
      if (password.length >= 8) strength++;
      if (password.match(/[A-Z]/)) strength++;
      if (password.match(/[0-9]/)) strength++;
      if (password.match(/[^A-Za-z0-9]/)) strength++;
      
      strengthIndicator.classList.remove('bg-danger', 'bg-warning', 'bg-success');
      
      if (strength < 2) {
        strengthIndicator.style.width = '25%';
        strengthIndicator.classList.add('bg-danger');
        strengthIndicator.textContent = 'Weak';
      } else if (strength < 4) {
        strengthIndicator.style.width = '50%';
        strengthIndicator.classList.add('bg-warning');
        strengthIndicator.textContent = 'Medium';
      } else {
        strengthIndicator.style.width = '100%';
        strengthIndicator.classList.add('bg-success');
        strengthIndicator.textContent = 'Strong';
      }
    });
  }
});
