/**
 * NIVARA — Client-side Interactivity & UI Utilities
 */

document.addEventListener('DOMContentLoaded', () => {
  // 1. Mobile Sidebar Toggle
  const sidebarToggle = document.getElementById('sidebarToggle');
  const appSidebar = document.getElementById('appSidebar');

  if (sidebarToggle && appSidebar) {
    sidebarToggle.addEventListener('click', (e) => {
      e.stopPropagation();
      appSidebar.classList.toggle('show');
    });

    // Close sidebar when clicking outside on mobile
    document.addEventListener('click', (e) => {
      if (window.innerWidth < 992 && appSidebar.classList.contains('show')) {
        if (!appSidebar.contains(e.target) && e.target !== sidebarToggle) {
          appSidebar.classList.remove('show');
        }
      }
    });
  }

  // 2. Family & Room Capacity Calculation
  const room = document.getElementById('room_id');
  const note = document.getElementById('capacityNote');
  const members = document.getElementById('members');
  const addMember = document.getElementById('addMember');

  function syncCapacity() {
    if (!room || !note) return;
    const selected = room.options[room.selectedIndex];
    const capacity = selected?.dataset?.capacity || '0';
    const current = members?.querySelectorAll('.member-row').length || 0;
    const remaining = Math.max(0, Number(capacity) - 1 - current);

    note.innerHTML = `Room capacity: <strong>${capacity} persons</strong> (Head uses 1). Remaining additional spots: <strong>${remaining}</strong>.`;
    if (addMember) {
      addMember.disabled = current >= Math.max(0, Number(capacity) - 1);
    }
  }

  function addMemberRow() {
    if (!members) return;
    const div = document.createElement('div');
    div.className = 'row g-2 member-row mb-2 align-items-center';
    div.innerHTML = `
      <div class="col-12 col-sm-7">
        <input class="form-control form-control-sm" name="member_name[]" placeholder="Member full name" maxlength="100" required>
      </div>
      <div class="col-8 col-sm-3">
        <input class="form-control form-control-sm" name="member_age[]" type="number" min="0" max="120" placeholder="Age" required>
      </div>
      <div class="col-4 col-sm-2 text-end">
        <button type="button" class="btn btn-danger-outline btn-sm w-100 remove-member">
          <i class="bi bi-x-lg"></i>
        </button>
      </div>
    `;
    div.querySelector('.remove-member').addEventListener('click', () => {
      div.remove();
      syncCapacity();
    });
    members.appendChild(div);
    syncCapacity();
  }

  addMember?.addEventListener('click', addMemberRow);
  room?.addEventListener('change', syncCapacity);
  syncCapacity();

  // 3. Confirmation Dialogs
  document.querySelectorAll('[data-confirm]').forEach(form => {
    form.addEventListener('submit', e => {
      if (!window.confirm(form.dataset.confirm)) {
        e.preventDefault();
      }
    });
  });

  // 4. Client-side Realtime Search & Filters

  // Room Table Filter
  const roomSearchInput = document.getElementById('roomSearchInput');
  const roomStatusFilter = document.getElementById('roomStatusFilter');
  const roomRows = document.querySelectorAll('.room-row');

  function filterRooms() {
    const query = roomSearchInput?.value.toLowerCase().trim() || '';
    const status = roomStatusFilter?.value || '';

    roomRows.forEach(row => {
      const text = row.textContent.toLowerCase();
      const rowStatus = row.dataset.status || '';
      const matchesQuery = !query || text.includes(query);
      const matchesStatus = !status || rowStatus === status;

      row.style.display = (matchesQuery && matchesStatus) ? '' : 'none';
    });
  }

  roomSearchInput?.addEventListener('input', filterRooms);
  roomStatusFilter?.addEventListener('change', filterRooms);

  // Tenant Table Filter
  const tenantSearchInput = document.getElementById('tenantSearchInput');
  const tenantRows = document.querySelectorAll('.tenant-row');

  tenantSearchInput?.addEventListener('input', () => {
    const query = tenantSearchInput.value.toLowerCase().trim();
    tenantRows.forEach(row => {
      const text = row.textContent.toLowerCase();
      row.style.display = (!query || text.includes(query)) ? '' : 'none';
    });
  });

  // Billing Table Filter
  const billSearchInput = document.getElementById('billSearchInput');
  const billStatusFilter = document.getElementById('billStatusFilter');
  const billRows = document.querySelectorAll('.bill-row');

  function filterBills() {
    const query = billSearchInput?.value.toLowerCase().trim() || '';
    const status = billStatusFilter?.value || '';

    billRows.forEach(row => {
      const text = row.textContent.toLowerCase();
      const rowStatus = row.dataset.status || '';
      const matchesQuery = !query || text.includes(query);
      const matchesStatus = !status || rowStatus === status;

      row.style.display = (matchesQuery && matchesStatus) ? '' : 'none';
    });
  }

  billSearchInput?.addEventListener('input', filterBills);
  billStatusFilter?.addEventListener('change', filterBills);
});
