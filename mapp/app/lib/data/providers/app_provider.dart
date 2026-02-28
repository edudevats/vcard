import 'package:flutter/foundation.dart';
import '../../core/network/api_client.dart';
import '../models/models.dart';

/// Provider general: dashboard, tarjetas, citas, tickets.
class AppProvider extends ChangeNotifier {
  // ── State ─────────────────────────────────────────────────────────────
  DashboardData? _dashboard;
  List<CardModel> _cards = [];
  List<ServiceModel> _services = [];
  List<AppointmentModel> _appointments = [];
  Map<String, dynamic>? _ticketsData;
  Map<String, dynamic>? _analyticsData;

  bool _loadingDashboard = false;
  bool _loadingCards = false;
  bool _loadingServices = false;
  bool _loadingAppointments = false;
  bool _loadingTickets = false;

  String? _error;

  // ── Getters ──────────────────────────────────────────────────────────────
  DashboardData? get dashboard => _dashboard;
  List<CardModel> get cards => _cards;
  List<ServiceModel> get services => _services;
  List<AppointmentModel> get appointments => _appointments;
  Map<String, dynamic>? get ticketsData => _ticketsData;
  Map<String, dynamic>? get analyticsData => _analyticsData;

  bool get loadingDashboard => _loadingDashboard;
  bool get loadingCards => _loadingCards;
  bool get loadingServices => _loadingServices;
  bool get loadingAppointments => _loadingAppointments;
  bool get loadingTickets => _loadingTickets;
  String? get error => _error;

  // ── Dashboard ────────────────────────────────────────────────────────────

  Future<void> fetchDashboard() async {
    _loadingDashboard = true;
    _error = null;
    notifyListeners();

    final res = await ApiClient.get('/dashboard');
    _loadingDashboard = false;

    if (res.success) {
      _dashboard = DashboardData.fromJson(res.data);
      _cards = _dashboard!.cards;
    } else {
      _error = res.error;
    }
    notifyListeners();
  }

  // ── Cards ────────────────────────────────────────────────────────────────

  Future<void> fetchCards() async {
    _loadingCards = true;
    notifyListeners();

    final res = await ApiClient.get('/cards');
    _loadingCards = false;

    if (res.success) {
      _cards = (res.data as List).map((c) => CardModel.fromJson(c)).toList();
    } else {
      _error = res.error;
    }
    notifyListeners();
  }

  Future<CardModel?> fetchCard(int cardId) async {
    final res = await ApiClient.get('/cards/$cardId');
    if (res.success) return CardModel.fromJson(res.data);
    _error = res.error;
    notifyListeners();
    return null;
  }

  Future<bool> togglePublish(int cardId) async {
    final res = await ApiClient.post('/cards/$cardId/toggle-publish');
    if (res.success) {
      // Update local list
      _cards = _cards.map((c) {
        if (c.id == cardId) {
          return CardModel.fromJson({
            ...{
              'id': c.id, 'slug': c.slug, 'title': c.title, 'name': c.name,
              'job_title': c.jobTitle, 'company': c.company, 'phone': c.phone,
              'email_public': c.emailPublic, 'website': c.website,
              'location': c.location, 'bio': c.bio,
              'avatar_url': c.avatarUrl, 'public_url': c.publicUrl,
              'created_at': c.createdAt, 'updated_at': c.updatedAt,
            },
            'is_public': res.data['is_public'],
          });
        }
        return c;
      }).toList();
      notifyListeners();
      return true;
    }
    _error = res.error;
    notifyListeners();
    return false;
  }

  // ── Services ─────────────────────────────────────────────────────────────

  Future<void> fetchServices(int cardId) async {
    _loadingServices = true;
    notifyListeners();

    final res = await ApiClient.get('/cards/$cardId/services');
    _loadingServices = false;

    if (res.success) {
      _services = (res.data as List).map((s) => ServiceModel.fromJson(s)).toList();
    } else {
      _error = res.error;
    }
    notifyListeners();
  }

  Future<bool> createService(int cardId, Map<String, dynamic> data) async {
    final res = await ApiClient.post('/cards/$cardId/services', body: data);
    if (res.success) {
      _services.add(ServiceModel.fromJson(res.data));
      notifyListeners();
      return true;
    }
    _error = res.error;
    notifyListeners();
    return false;
  }

  Future<bool> updateService(int serviceId, Map<String, dynamic> data) async {
    final res = await ApiClient.put('/services/$serviceId', body: data);
    if (res.success) {
      final updated = ServiceModel.fromJson(res.data);
      _services = _services.map((s) => s.id == serviceId ? updated : s).toList();
      notifyListeners();
      return true;
    }
    _error = res.error;
    notifyListeners();
    return false;
  }

  Future<bool> deleteService(int serviceId) async {
    final res = await ApiClient.delete('/services/$serviceId');
    if (res.success) {
      _services.removeWhere((s) => s.id == serviceId);
      notifyListeners();
      return true;
    }
    _error = res.error;
    notifyListeners();
    return false;
  }

  // ── Appointments ──────────────────────────────────────────────────────────

  Future<void> fetchAppointments({String? status}) async {
    _loadingAppointments = true;
    notifyListeners();

    final params = status != null ? {'status': status} : null;
    final res = await ApiClient.get('/appointments', queryParams: params);
    _loadingAppointments = false;

    if (res.success) {
      _appointments = (res.data as List)
          .map((a) => AppointmentModel.fromJson(a))
          .toList();
    } else {
      _error = res.error;
    }
    notifyListeners();
  }

  Future<bool> updateAppointmentStatus(int aptId, String action,
      {String? reason}) async {
    final body = reason != null ? {'reason': reason} : null;
    final res = await ApiClient.post('/appointments/$aptId/$action', body: body);
    if (res.success) {
      final updated = AppointmentModel.fromJson(res.data);
      _appointments =
          _appointments.map((a) => a.id == aptId ? updated : a).toList();
      notifyListeners();
      return true;
    }
    _error = res.error;
    notifyListeners();
    return false;
  }

  Future<Map<String, int>> fetchAppointmentStats() async {
    final res = await ApiClient.get('/appointments/stats');
    if (res.success) {
      return {
        'total': res.data['total'] ?? 0,
        'pending': res.data['pending'] ?? 0,
        'confirmed': res.data['confirmed'] ?? 0,
        'today': res.data['today'] ?? 0,
      };
    }
    return {};
  }

  // ── Tickets ───────────────────────────────────────────────────────────────

  Future<void> fetchTickets({String status = 'all'}) async {
    _loadingTickets = true;
    notifyListeners();

    final res = await ApiClient.get('/tickets',
        queryParams: status != 'all' ? {'status': status} : null);
    _loadingTickets = false;

    if (res.success) {
      _ticketsData = res.data;
    } else {
      _error = res.error;
    }
    notifyListeners();
  }

  Future<Map<String, dynamic>?> callNextTicket() async {
    final res = await ApiClient.post('/tickets/call-next');
    if (res.success) {
      await fetchTickets();
      return res.data;
    }
    _error = res.error;
    notifyListeners();
    return null;
  }

  Future<bool> updateTicketStatus(int ticketId, String action) async {
    final res = await ApiClient.post('/tickets/$ticketId/$action');
    if (res.success) {
      await fetchTickets();
      return true;
    }
    _error = res.error;
    notifyListeners();
    return false;
  }

  Future<bool> toggleAccepting() async {
    final res = await ApiClient.post('/tickets/toggle-accepting');
    if (res.success) {
      if (_ticketsData != null) {
        _ticketsData!['is_accepting'] = res.data['is_accepting'];
        notifyListeners();
      }
      return true;
    }
    _error = res.error;
    notifyListeners();
    return false;
  }

  // ── Analytics ─────────────────────────────────────────────────────────────

  Future<void> fetchAnalytics() async {
    final res = await ApiClient.get('/analytics');
    if (res.success) {
      _analyticsData = res.data;
      notifyListeners();
    }
  }

  // ── Utils ─────────────────────────────────────────────────────────────────

  void clearError() {
    _error = null;
    notifyListeners();
  }

  void reset() {
    _dashboard = null;
    _cards = [];
    _services = [];
    _appointments = [];
    _ticketsData = null;
    _analyticsData = null;
    notifyListeners();
  }
}
