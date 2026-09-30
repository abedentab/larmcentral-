# Larmcentral – provmodell

Detta repository används som arbetsyta för Home Assistant-projektet **Larmcentral**.

## Larmdefinition

```yaml
- entity: switch.kamera_stolpe_rorelselarm
  namn: Kamera stolpe rörelselarm
  niva: gul
  tid_till_rod: 5
```

## Regler

- `niva: gul` → aktivt larm visas som gult.
- `niva: rod` → aktivt larm visas direkt som rött.
- `tid_till_rod: 5` → ett gult larm blir rött efter 5 minuter om felet fortfarande är aktivt.
- `tid_till_rod: 0` → ingen tidseskalering.
- När felet upphör tas larmet bort från aktiva larm.
- Händelsen ska sparas i Larmhistoriken.
- Befintliga fungerande delar i Home Assistant ska behållas oförändrade tills en ändring uttryckligen behövs.

## Status

Första provmodellen är skapad i GitHub. Ingen Home Assistant-konfiguration har ändrats.
