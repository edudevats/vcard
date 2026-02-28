import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import 'package:url_launcher/url_launcher.dart';

/// Formatea una fecha ISO a formato legible en español.
String formatDate(String? iso, {String fallback = '-'}) {
  if (iso == null || iso.isEmpty) return fallback;
  try {
    final dt = DateTime.parse(iso).toLocal();
    return DateFormat('dd/MM/yyyy', 'es').format(dt);
  } catch (_) {
    return fallback;
  }
}

/// Formatea fecha y hora ISO.
String formatDateTime(String? iso, {String fallback = '-'}) {
  if (iso == null || iso.isEmpty) return fallback;
  try {
    final dt = DateTime.parse(iso).toLocal();
    return DateFormat('dd/MM/yyyy HH:mm', 'es').format(dt);
  } catch (_) {
    return fallback;
  }
}

/// Formatea precio con símbolo de moneda.
String formatPrice(dynamic price, {String currency = '\$'}) {
  if (price == null) return 'Consultar';
  final n = double.tryParse(price.toString()) ?? 0;
  return '$currency${NumberFormat('#,##0.00').format(n)}';
}

/// Abre una URL en el navegador externo.
Future<void> openUrl(String url) async {
  final uri = Uri.parse(url);
  if (await canLaunchUrl(uri)) {
    await launchUrl(uri, mode: LaunchMode.externalApplication);
  }
}

/// Abre marcador telefónico.
Future<void> callPhone(String phone) async {
  final uri = Uri(scheme: 'tel', path: phone.replaceAll(' ', ''));
  if (await canLaunchUrl(uri)) await launchUrl(uri);
}

/// Abre WhatsApp con mensaje pre-llenado.
Future<void> openWhatsApp(String phone, {String message = ''}) async {
  final clean = phone.replaceAll(RegExp(r'[^\d+]'), '');
  final encoded = Uri.encodeComponent(message);
  final uri = Uri.parse('https://wa.me/$clean?text=$encoded');
  if (await canLaunchUrl(uri)) {
    await launchUrl(uri, mode: LaunchMode.externalApplication);
  }
}

/// Muestra un SnackBar estilizado.
void showSnack(BuildContext context, String message,
    {bool isError = false}) {
  ScaffoldMessenger.of(context).showSnackBar(
    SnackBar(
      content: Text(message),
      backgroundColor: isError ? const Color(0xFFEF4444) : const Color(0xFF10B981),
      behavior: SnackBarBehavior.floating,
      duration: const Duration(seconds: 3),
    ),
  );
}

/// Muestra diálogo de confirmación y retorna true/false.
Future<bool> confirmDialog(
  BuildContext context, {
  required String title,
  required String message,
  String confirmText = 'Confirmar',
  String cancelText = 'Cancelar',
  bool isDestructive = false,
}) async {
  final result = await showDialog<bool>(
    context: context,
    builder: (_) => AlertDialog(
      title: Text(title),
      content: Text(message),
      actions: [
        TextButton(
          onPressed: () => Navigator.pop(context, false),
          child: Text(cancelText),
        ),
        TextButton(
          onPressed: () => Navigator.pop(context, true),
          style: TextButton.styleFrom(
            foregroundColor: isDestructive ? const Color(0xFFEF4444) : null,
          ),
          child: Text(confirmText),
        ),
      ],
    ),
  );
  return result ?? false;
}

/// Capitaliza la primera letra de un texto.
String capitalize(String? text) {
  if (text == null || text.isEmpty) return '';
  return text[0].toUpperCase() + text.substring(1);
}

/// Obtiene las iniciales de un nombre (máx 2 caracteres).
String initials(String? name) {
  if (name == null || name.isEmpty) return '?';
  final parts = name.trim().split(' ');
  if (parts.length == 1) return parts[0][0].toUpperCase();
  return '${parts[0][0]}${parts[1][0]}'.toUpperCase();
}
