<script setup>
import { computed, onMounted, ref } from 'vue'

const labels = {
  es: { eyebrow: 'MIRADOR AZUL  /  OPERACIONES', title: 'Cada solicitud,', title2: 'bajo control.', subtitle: 'Un tablero para dar seguimiento a cada huésped, desde su primera consulta hasta el cierre.', new: 'Nueva solicitud', guest: 'Nombre del huésped', service: 'Servicio', arrival: 'Fecha de llegada', note: 'Nota interna', create: 'Crear solicitud', all: 'Todas', board: 'Tablero de solicitudes', empty: 'No hay solicitudes en este estado.', loadError: 'No se pudo conectar con DynamoDB Local. Inicia el servicio y vuelve a cargar.', saveError: 'No se pudo guardar. Verifica los datos e intenta de nuevo.', status: 'Estado', date: 'Llegada', requests: 'solicitudes', demo: 'PORTAFOLIO · DATOS FICTICIOS', refresh: 'Actualizar', statuses: { new: 'Nueva', contacted: 'Contactado', confirmed: 'Confirmada', closed: 'Cerrada' } },
  en: { eyebrow: 'MIRADOR AZUL  /  OPERATIONS', title: 'Every request,', title2: 'in its place.', subtitle: 'One board to follow every guest from the first inquiry to the final update.', new: 'New request', guest: 'Guest name', service: 'Service', arrival: 'Arrival date', note: 'Internal note', create: 'Create request', all: 'All', board: 'Request board', empty: 'No requests in this status.', loadError: 'Could not connect to DynamoDB Local. Start the service and reload.', saveError: 'Could not save. Check the details and try again.', status: 'Status', date: 'Arrival', requests: 'requests', demo: 'PORTFOLIO · FICTIONAL DATA', refresh: 'Refresh', statuses: { new: 'New', contacted: 'Contacted', confirmed: 'Confirmed', closed: 'Closed' } }
}
const locale = ref('es')
const copy = computed(() => labels[locale.value])
const requests = ref([])
const filter = ref('all')
const busy = ref(false)
const error = ref('')
const formOpen = ref(false)
const form = ref({ guest: '', service: '', arrival: '', note: '' })
const statuses = ['new', 'contacted', 'confirmed', 'closed']
const visible = computed(() => filter.value === 'all' ? requests.value : requests.value.filter(item => item.status === filter.value))

async function load() {
  error.value = ''
  try {
    const response = await fetch('/api/requests')
    if (!response.ok) throw new Error('load')
    requests.value = await response.json()
  } catch { error.value = copy.value.loadError }
}

async function create() {
  busy.value = true; error.value = ''
  try {
    const response = await fetch('/api/requests', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(form.value) })
    if (!response.ok) throw new Error('create')
    form.value = { guest: '', service: '', arrival: '', note: '' }
    formOpen.value = false
    await load()
  } catch { error.value = copy.value.saveError }
  finally { busy.value = false }
}

async function changeStatus(item, status) {
  if (status === item.status) return
  busy.value = true; error.value = ''
  try {
    const response = await fetch(`/api/requests/${encodeURIComponent(item.request_id)}`, { method: 'PATCH', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ status, version: item.version }) })
    if (!response.ok) throw new Error('update')
    await load()
  } catch { error.value = copy.value.saveError; await load() }
  finally { busy.value = false }
}

onMounted(load)
</script>

<template>
  <div class="shell">
    <aside class="rail"><div class="mark">M<span>✦</span></div><div class="rail-line"></div><span class="rail-label">MIRADOR AZUL</span><span class="rail-index">01 / 04</span></aside>
    <main>
      <header class="topbar"><div class="wordmark">MIRADOR AZUL <span>Operations desk</span></div><div class="top-actions"><span class="demo-tag">{{ copy.demo }}</span><button class="locale" @click="locale = locale === 'es' ? 'en' : 'es'">{{ locale.toUpperCase() }} <span>↗</span></button></div></header>
      <section class="hero"><div class="hero-copy"><div class="eyebrow"><span class="signal"></span>{{ copy.eyebrow }}</div><h1>{{ copy.title }}<br><em>{{ copy.title2 }}</em></h1><p>{{ copy.subtitle }}</p><div class="hero-actions"><button class="primary" @click="formOpen = !formOpen">{{ copy.new }} <span>↗</span></button><button class="quiet" @click="load">{{ copy.refresh }} ↻</button></div></div><div class="hero-visual" aria-hidden="true"><div class="sun"></div><div class="ridge one"></div><div class="ridge two"></div><div class="water"></div><div class="visual-caption">SERVICE · STAY · FOLLOW THROUGH</div></div></section>
      <div v-if="error" role="alert" class="alert">{{ error }}</div>
      <section v-if="formOpen" class="form-card"><div class="section-heading"><div><small>01 / CAPTURE</small><h2>{{ copy.new }}</h2></div><button class="close" aria-label="Close" @click="formOpen = false">×</button></div><form @submit.prevent="create"><div class="form-grid"><label>{{ copy.guest }}<input v-model.trim="form.guest" required minlength="2" maxlength="80" placeholder="María López"></label><label>{{ copy.service }}<input v-model.trim="form.service" required minlength="2" maxlength="80" placeholder="Airport transfer"></label><label>{{ copy.arrival }}<input v-model="form.arrival" required type="date"></label><label>{{ copy.note }}<input v-model.trim="form.note" maxlength="240" placeholder="Optional"></label></div><button class="primary" :disabled="busy">{{ copy.create }} <span>↗</span></button></form></section>
      <section class="board"><div class="section-heading"><div><small>02 / PIPELINE</small><h2>{{ copy.board }} <span>{{ requests.length.toString().padStart(2, '0') }}</span></h2></div><div class="board-count">{{ visible.length }} {{ copy.requests }}</div></div><div class="tabs" role="tablist"><button v-for="key in ['all', ...statuses]" :key="key" :class="{ active: filter === key }" role="tab" :aria-selected="filter === key" @click="filter = key">{{ key === 'all' ? copy.all : copy.statuses[key] }} <span>{{ key === 'all' ? requests.length : requests.filter(item => item.status === key).length }}</span></button></div><div v-if="!visible.length" class="empty"><div>✦</div>{{ copy.empty }}</div><div v-else class="cards"><article v-for="(item, index) in visible" :key="item.request_id" class="request-card"><span class="folio">{{ String(index + 1).padStart(2, "0") }}</span><div class="card-head"><div class="card-symbol">{{ item.guest.slice(0, 1).toUpperCase() }}</div><span class="status" :class="item.status">{{ copy.statuses[item.status] }}</span></div><h3>{{ item.guest }}</h3><p>{{ item.service }}</p><div v-if="item.note" class="note">“{{ item.note }}”</div><div class="card-footer"><div><small>{{ copy.date }}</small><strong>{{ item.arrival }}</strong></div><label><span class="sr-only">{{ copy.status }}</span><select :value="item.status" :disabled="busy" @change="changeStatus(item, $event.target.value)"><option v-for="status in statuses" :key="status" :value="status">{{ copy.statuses[status] }}</option></select></label></div></article></div></section>
      <footer><span>© MIRADOR AZUL · FICTIONAL HOTEL</span><span>DYNAMODB LOCAL / FASTAPI / VUE</span></footer>
    </main>
  </div>
</template>
