class LarmcentralAddCard extends HTMLElement {
  setConfig(config) {
    this._config = config || {};
    if (!this._rendered) this._render();
  }

  set hass(hass) {
    this._hass = hass;
  }

  getCardSize() {
    return 2;
  }

  _render() {
    this._rendered = true;
    this.innerHTML = `
      <ha-card>
        <button id="add" type="button">
          <ha-icon icon="mdi:plus-circle"></ha-icon>
          <span>Skapa nytt larm</span>
        </button>
      </ha-card>
      <style>
        ha-card { overflow: hidden; }
        button {
          width: 100%;
          min-height: 104px;
          border: 0;
          background: transparent;
          color: var(--primary-text-color);
          cursor: pointer;
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          gap: 10px;
          font: inherit;
        }
        ha-icon {
          --mdc-icon-size: 36px;
          color: var(--primary-color);
        }
        span { font-size: 16px; font-weight: 500; }
      </style>
    `;

    this.querySelector("#add").addEventListener("click", () => this._openFlow());
  }

  async _openFlow() {
    if (!this._hass) return;

    try {
      const flow = await this._hass.callWS({
        type: "config_entries/flow/init",
        handler: "larmcentral",
        show_advanced_options: false,
      });

      // Home Assistant's dialog component is normally already loaded after
      // config/integrations has been used. If it is not, use HA's normal
      // integrations page once to load it, without creating a second flow.
      if (!customElements.get("dialog-data-entry-flow")) {
        history.pushState(
          null,
          "",
          "/config/integrations/dashboard"
        );
        window.dispatchEvent(new Event("location-changed"));
        return;
      }

      this.dispatchEvent(
        new CustomEvent("show-dialog", {
          bubbles: true,
          composed: true,
          detail: {
            dialogTag: "dialog-data-entry-flow",
            dialogImport: async () => {},
            dialogParams: {
              continueFlowId: flow.flow_id,
            },
          },
        })
      );
    } catch (err) {
      console.error("Larmcentral: kunde inte öppna nytt larm", err);
    }
  }
}

if (!customElements.get("larmcentral-add-card")) {
  customElements.define("larmcentral-add-card", LarmcentralAddCard);
}

window.customCards = window.customCards || [];
if (!window.customCards.some((card) => card.type === "larmcentral-add-card")) {
  window.customCards.push({
    type: "larmcentral-add-card",
    name: "Larmcentral – Skapa nytt larm",
    description: "Startar Larmcentrals config flow direkt.",
  });
}
