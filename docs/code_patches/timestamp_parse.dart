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
