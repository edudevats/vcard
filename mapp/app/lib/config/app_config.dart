/// Configuración global de la aplicación ATScard.
/// Cambia [baseUrl] a la IP/dominio del servidor Flask.
class AppConfig {
  // ── Servidor ──────────────────────────────────────────────────────────
  /// URL base del servidor Flask. En desarrollo usa la IP de tu máquina.
  /// Ejemplo: 'http://192.168.1.100:5000'
  static const String baseUrl = 'http://10.0.2.2:5000'; // Android Emulator

  /// Prefijo de la API móvil
  static const String apiPrefix = '/api/mobile/v1';

  static String get apiUrl => '$baseUrl$apiPrefix';

  // ── Timeouts ──────────────────────────────────────────────────────────
  static const Duration connectTimeout = Duration(seconds: 15);
  static const Duration receiveTimeout = Duration(seconds: 30);

  // ── App Info ──────────────────────────────────────────────────────────
  static const String appName = 'ATScard';
  static const String appVersion = '1.0.0';
}
