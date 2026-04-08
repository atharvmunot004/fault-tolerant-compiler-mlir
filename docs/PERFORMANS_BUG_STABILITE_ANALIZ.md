# Randevux – Performans, Hata, Stabilite ve Mantık Analizi

Bu belge, uygulamanın performans, bug, stabilite ve mantıksal tutarlılık açısından derinlemesine incelemesinin özetidir. **Uygulama adımları** bölümünde 1 ve 2 numaralı iyileştirmelerin nasıl yapılacağı adım adım anlatılmaktadır.

---

## 1. Performans

### 1.1 shrinkWrap + NeverScrollableScrollPhysics (liste sanallaştırma)

Bu kombinasyon tüm öğeleri aynı anda layout'a sokar; uzun listelerde jank ve bellek artışına yol açar.

| Dosya | Satır | Açıklama |
|-------|--------|----------|
| `lib/features/dashboard/presentation/dashboard_page.dart` | ~835, ~1518 | Arama sonuçları ve rapor “dönem randevuları” listesi: `ListView.builder(shrinkWrap: true)` – uzun listelerde sliver/tek scroll düşünülmeli. |
| `lib/features/appointments/presentation/add_appointment_sheet.dart` | ~628 | Bir liste `shrinkWrap: true` ile kullanılıyor. |
| `lib/features/public_booking/presentation/public_booking_page.dart` | 408–410 | Hizmet listesi: `ListView.builder(shrinkWrap: true, physics: NeverScrollableScrollPhysics())` – hizmet sayısı azsa kabul edilebilir; çoksa CustomScrollView + SliverList ile tek scroll'a alınabilir. |

### 1.2 Üst seviyede çok sayıda ref.watch (büyük rebuild'ler)

| Dosya | Durum |
|-------|--------|
| `dashboard_page.dart` | Özet kartları için watch _SummaryCards içine alındı; diğerleri hâlâ ana build'de. |
| `add_appointment_sheet.dart` | Birçok provider watch; ref.listen veya daha küçük Consumer widget’lara bölme düşünülebilir. |
| `customers_page.dart` | Filtre/değişkenler değişince tüm sayfa rebuild. |
| `settings_sections.dart` | İşletme ve Google Takvim bölümleri birçok provider watch ediyor. |

### 1.3 Büyük widget ağacı

- `dashboard_page.dart` tek dosyada ~2300 satır; parçalara bölmek hem rebuild maliyeti hem bakım için faydalı.

---

## 2. Hatalar / Stabilite

### 2.1 Timestamp / DateTime parsing (cast ile fırlatma riski)

Firestore’dan gelen alan bazen `Timestamp` değil (örn. int, String, Map) olabilir; doğrudan `as Timestamp?` kullanımı **runtime’da cast hatası** verebilir.

| Dosya | Satır | Risk |
|-------|--------|------|
| `appointment_repository.dart` | 154 | `data['startTime'] as Timestamp?` – startTime farklı tipte olursa hata. |
| `appointment_model.dart` | 110, 128, 130 | `fromMap` içinde startTime, endTime, createdAt doğrudan cast. |
| `app_notification.dart` | 29–30 | createdAt, readAt. |
| `employee_model.dart` | 79 | createdAt. |
| `room_model.dart` | 31 | createdAt. |
| `business_model.dart` | 150–151 | **Güvenli:** `is Timestamp` kontrolü sonrası cast. |

---

## 3. Mantık / Tutarlılık

### 3.1 Mutasyon sonrası provider invalidate

- **Müşteri detay sayfasında randevu iptal / durum değişikliği (popup menü):** `updateAppointmentStatus` sonrası `customerAppointmentsProvider(widget.customer.id)` ve `dashboardAppointmentsProvider(businessId)` invalidate **edilmiyor**. Firestore stream kullanılıyorsa zamanla güncellenir; hemen UI senkronu için bu iki provider’ın invalidate edilmesi önerilir.

---

## Uygulama adımları

### Adım 1: Timestamp/DateTime güvenli parse

**1.1 Ortak yardımcı dosyası**

Projede `lib/core/utils/timestamp_parse.dart` (veya `lib/core/utils/firestore_parse.dart`) oluşturun. Referans kodu bu depoda `docs/code_patches/timestamp_parse.dart` dosyasında bulunur; projenize kopyalayıp import path'ini (ör. `package:randevux/core/utils/timestamp_parse.dart`) kendi paket adınıza göre düzenleyin.

```dart
import 'package:cloud_firestore/cloud_firestore.dart';

/// Firestore'dan gelen tarih alanını güvenli parse eder.
/// Timestamp, int (ms), String (ISO), DateTime ve null kabul eder; bilinmeyen tiplerde null döner.
DateTime? parseTimestamp(dynamic v) {
  if (v == null) return null;
  if (v is Timestamp) return v.toDate();
  if (v is DateTime) return v;
  if (v is int) return DateTime.fromMillisecondsSinceEpoch(v);
  if (v is String) return DateTime.tryParse(v);
  return null;
}
```

**1.2 appointment_model.dart**

- `import 'package:cloud_firestore/cloud_firestore.dart';` yanına (veya uygun yere) core util import ekleyin:  
  `import 'package:randevux/core/utils/timestamp_parse.dart';`  
  (Proje adına göre `randevux` yerine gerçek paket adınızı yazın.)
- `_parseTimestamp` static metodunu kaldırıp tüm tarih alanlarında `parseTimestamp` kullanın. Örnek:

```dart
// fromMap içinde:
final startTime = parseTimestamp(map['startTime']) ?? appointmentMissingDateSentinel;
// ...
endTime: parseTimestamp(map['endTime']) ?? startTime,
createdAt: parseTimestamp(map['createdAt']) ?? appointmentMissingDateSentinel,
smsReminder1DaySentAt: parseTimestamp(map['smsReminder1DaySentAt']),
// ... diğer opsiyonel alanlar da parseTimestamp(map['...'])
```

**1.3 appointment_repository.dart**

- `timestamp_parse.dart` import edin.
- `_mapAppointmentDocs` içinde `data['endTime']` hesaplanırken (satır ~153–158) `data['startTime']` için cast yerine güvenli parse kullanın. Örnek:

```dart
if (data['endTime'] == null) {
  final startDt = parseTimestamp(data['startTime']);
  data['endTime'] = startDt != null
      ? Timestamp.fromDate(startDt.add(const Duration(minutes: 30)))
      : Timestamp.now();
}
```

Böylece `data['startTime'] as Timestamp?` satırı kaldırılmış olur.

**1.4 app_notification.dart**

- `parseTimestamp` import edin.
- `createdAt` ve `readAt` atamalarında cast yerine:  
  `final createdAt = parseTimestamp(map['createdAt']) ?? DateTime.now();`  
  `final readAt = parseTimestamp(map['readAt']);`

**1.5 employee_model.dart**

- `parseTimestamp` import edin.
- `createdAt` için: `parseTimestamp(map['createdAt']) ?? ...` (mevcut sentinel veya null).

**1.6 room_model.dart**

- `parseTimestamp` import edin.
- `createdAt` için: `parseTimestamp(map['createdAt']) ?? ...`

---

### Adım 2: Müşteri detay – randevu iptal/durum değişikliği sonrası invalidate

**Dosya:** `lib/features/customers/presentation/customer_detail_page.dart`

**Yer:** Popup menüden randevu iptal edildiğinde veya durum değiştirildiğinde (`updateAppointmentStatus` çağrıldıktan sonra).

**Yapılacak:** Aynı blok içinde (try sonrası, başarılı güncellemeden hemen sonra) şu invalidate’leri ekleyin:

```dart
final businessId = ref.read(currentBusinessIdProvider);
if (businessId != null && businessId.isNotEmpty) {
  ref.invalidate(customerAppointmentsProvider(widget.customer.id));
  ref.invalidate(dashboardAppointmentsProvider(businessId));
}
```

- **İptal (cancelled) dalı:** `updateAppointmentStatus(..., newStatus: 'cancelled')` ve ilgili takvim/reminder işlemleri tamamlandıktan sonra yukarıdaki invalidate’leri ekleyin.
- **Diğer durum değişiklikleri (scheduled, completed vb.):** `updateAppointmentStatus` çağrıldıktan sonra aynı invalidate’leri ekleyin.

Böylece müşteri detay sayfasındaki randevu listesi ve dashboard listesi hemen güncellenir.

---

## Özet öncelik tablosu

| Öncelik | Kategori | Öneri |
|---------|----------|--------|
| **Yüksek** | Stabilite | Timestamp/DateTime parsing’i güvenli hale getir (Adım 1). |
| **Orta** | Mantık | Müşteri detayda randevu iptal/durum değişikliği sonrası provider invalidate (Adım 2). |
| Orta | Performans | Kalan shrinkWrap listeleri ve watch’ları iyileştir. |
| Düşük | Performans | dashboard_page’i parçalara böl, const geçişi. |
