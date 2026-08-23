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
    note.textContent = `Capacity: ${capacity}. Family head uses 1 place. Additional members: ${Math.max(0, Number(capacity)-1-current)} remaining.`;
    if (addMember) addMember.disabled = current >= Math.max(0, Number(capacity)-1);
  }

  function addMemberRow() {
    const div = document.createElement('div');
    div.className = 'row g-2 member-row mb-2';
    div.innerHTML = `<div class="col-md-7"><input class="form-control" name="member_name[]" placeholder="Member name" maxlength="100"></div><div class="col-md-3"><input class="form-control" name="member_age[]" type="number" min="0" max="120" placeholder="Age"></div><div class="col-md-2"><button type="button" class="btn btn-outline-danger w-100 remove-member">Remove</button></div>`;
    div.querySelector('.remove-member').addEventListener('click', () => { div.remove(); syncCapacity(); });
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
