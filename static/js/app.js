document.addEventListener('DOMContentLoaded', () => {
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
    
    note.innerHTML = `<i class="bi bi-info-circle me-1"></i> Room Capacity: <strong>${capacity}</strong>. Family head uses 1 spot. Additional member spots remaining: <strong>${remaining}</strong>.`;
    if (addMember) addMember.disabled = current >= Math.max(0, Number(capacity) - 1);
  }

  function addMemberRow() {
    const div = document.createElement('div');
    div.className = 'row g-2 member-row mb-2 align-items-center';
    div.innerHTML = `
      <div class="col-md-7">
        <div class="input-group">
          <span class="input-group-text bg-light"><i class="bi bi-person"></i></span>
          <input class="form-control" name="member_name[]" placeholder="Full Name" maxlength="100" required>
        </div>
      </div>
      <div class="col-md-3">
        <input class="form-control" name="member_age[]" type="number" min="0" max="120" placeholder="Age" required>
      </div>
      <div class="col-md-2">
        <button type="button" class="btn btn-outline-danger w-100 remove-member">
          <i class="bi bi-trash me-1"></i> Remove
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

  document.querySelectorAll('[data-confirm]').forEach(form => {
    form.addEventListener('submit', e => {
      if (!window.confirm(form.dataset.confirm)) e.preventDefault();
    });
  });
});
