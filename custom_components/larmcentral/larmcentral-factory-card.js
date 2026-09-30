class LarmcentralFactoryCard extends HTMLElement {
  setConfig(config) {
    this.config = config || {};
    this._name = "";
    this._entity = "";
    this._trigger = "on";
    this._level = "yellow";
    this._delay = 5;
    this._enabled = true;
    this._notify = true;
    this._render();
  }

  set hass(hass) {
    this._hass = hass;
    if (!this._rendered) this._render();
  }

  getCardSize() { return 8; }

  _render() {
    if (this._rendered) return;
    this._rendered = true;
    this.innerHTML = `
      <ha-card header="Nytt larm">
        <div class="content">
          <ha-textfield id="name" label="Namn på larmet"></ha-textfield>
          <ha-entity-picker id="entity" label="Larmkälla" allow-custom-entity></ha-entity-picker>
          <ha-textfield id="trigger" label="Larm när tillståndet är" value="on"></ha-textfield>

          <label>Startnivå</label>
          <select id="level">
            <option value="yellow">🟨 Gul</option>
            <option value="red">🟥 Röd</option>
          </select>

          <ha-textfield id="delay" label="🟥 Rött efter (minuter)" type="number" value="5"></ha-textfield>

          <div class="row"><span>Övervakning aktiv</span><ha-switch id="enabled" checked></ha-switch></div>
          <div class="row"><span>Mobilavisering vid rött</span><ha-switch id="notify" checked></ha-switch></div>

          <mwc-button id="add" raised>LÄGG TILL</mwc-button>
          <div id="message"></div>
        </div>
      </ha-card>
      <style>
        .content { padding: 16px; display: grid; gap: 16px; }
        ha-textfield, ha-entity-picker, select { width: 100%; }
        select { box-sizing: border-box; min-height: 48px; padding: 0 12px; border: 1px solid var(--divider-color); border-radius: 4px; background: var(--card-background-color); color: var(--primary-text-color); font-size: 16px; }
        label { color: var(--secondary-text-color); font-size: 12px; margin-bottom: -12px; }
        .row { display: flex; align-items: center; justify-content: space-between; min-height: 40px; }
        mwc-button { justify-self: end; }
        #message { min-height: 20px; color: var(--secondary-text-color); }
      </style>`;

    const q = (id) => this.querySelector("#" + id);
    const picker = q("entity");
    if (picker && this._hass) picker.hass = this._hass;

    q("level").addEventListener("change", (e) => {
      q("delay").disabled = e.target.value === "red";
    });

    q("add").addEventListener("click", async () => {
      const message = q("message");
      const name = q("name").value.trim();
      const entity = q("entity").value;
      if (!name || !entity) {
        message.textContent = "Fyll i namn och larmkälla.";
        return;
      }
      const data = {
        name,
        entity,
        trigger_state: q("trigger").value.trim() || "on",
        start_level: q("level").value,
        red_delay: Number(q("delay").value || 0),
        enabled: q("enabled").checked,
        notify_red: q("notify").checked
      };
      try {
        q("add").disabled = true;
        message.textContent = "Skapar larm…";
        await this._hass.callService("larmcentral", "add_alarm", data);
        message.textContent = "Larmet är tillagt.";
        q("name").value = "";
        q("entity").value = "";
      } catch (err) {
        message.textContent = "Kunde inte skapa larmet.";
      } finally {
        q("add").disabled = false;
      }
    });
  }

  updated() {
    const picker = this.querySelector("#entity");
    if (picker && this._hass) picker.hass = this._hass;
  }
}
customElements.define("larmcentral-factory-card", LarmcentralFactoryCard);
window.customCards = window.customCards || [];
window.customCards.push({
  type: "larmcentral-factory-card",
  name: "Larmcentral – Nytt larm",
  description: "Skapar nya larm direkt i Larmcentral."
});
