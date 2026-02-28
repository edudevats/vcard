import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../../core/theme/app_theme.dart';
import '../../../core/utils/helpers.dart';
import '../../../data/providers/app_provider.dart';
import '../../../data/models/models.dart';
import '../../widgets/common/widgets.dart';

class AppointmentsScreen extends StatefulWidget {
  const AppointmentsScreen({super.key});

  @override
  State<AppointmentsScreen> createState() => _AppointmentsScreenState();
}

class _AppointmentsScreenState extends State<AppointmentsScreen>
    with SingleTickerProviderStateMixin {
  late TabController _tabs;
  final _statusFilters = const ['all', 'pending', 'confirmed', 'completed', 'cancelled'];
  final _statusLabels = const ['Todas', 'Pendientes', 'Confirmadas', 'Completadas', 'Canceladas'];

  int _selectedTab = 0;

  @override
  void initState() {
    super.initState();
    _tabs = TabController(length: _statusFilters.length, vsync: this);
    _tabs.addListener(() {
      if (!_tabs.indexIsChanging) {
        setState(() => _selectedTab = _tabs.index);
        final status = _statusFilters[_tabs.index];
        context.read<AppProvider>().fetchAppointments(
              status: status == 'all' ? null : status,
            );
      }
    });
    WidgetsBinding.instance.addPostFrameCallback((_) {
      context.read<AppProvider>().fetchAppointments();
    });
  }

  @override
  void dispose() {
    _tabs.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final provider = context.watch<AppProvider>();

    return Scaffold(
      appBar: AppBar(
        title: const Text('Citas'),
        bottom: TabBar(
          controller: _tabs,
          isScrollable: true,
          tabAlignment: TabAlignment.start,
          tabs: _statusLabels.map((l) => Tab(text: l)).toList(),
        ),
      ),
      body: provider.loadingAppointments
          ? const ShimmerList(count: 5, itemHeight: 100)
          : provider.appointments.isEmpty
              ? EmptyState(
                  icon: Icons.event_busy_outlined,
                  title: 'Sin citas',
                  subtitle: 'Las citas aparecerán aquí cuando los clientes reserven.',
                )
              : RefreshIndicator(
                  onRefresh: () {
                    final status = _statusFilters[_selectedTab];
                    return context.read<AppProvider>().fetchAppointments(
                          status: status == 'all' ? null : status,
                        );
                  },
                  child: ListView.builder(
                    padding: const EdgeInsets.all(16),
                    itemCount: provider.appointments.length,
                    itemBuilder: (_, i) =>
                        _AppointmentCard(apt: provider.appointments[i]),
                  ),
                ),
    );
  }
}

class _AppointmentCard extends StatelessWidget {
  final AppointmentModel apt;
  const _AppointmentCard({required this.apt});

  Future<void> _action(BuildContext context, String action) async {
    String? reason;
    if (action == 'cancel') {
      reason = await _askReason(context);
      if (reason == null) return;
    }

    final provider = context.read<AppProvider>();
    final ok = await provider.updateAppointmentStatus(apt.id, action, reason: reason);

    if (!context.mounted) return;
    showSnack(
      context,
      ok ? 'Cita actualizada' : provider.error ?? 'Error',
      isError: !ok,
    );
  }

  Future<String?> _askReason(BuildContext context) async {
    final ctrl = TextEditingController();
    return showDialog<String>(
      context: context,
      builder: (_) => AlertDialog(
        title: const Text('Razón de cancelación'),
        content: TextField(
          controller: ctrl,
          decoration: const InputDecoration(
            hintText: 'Motivo (opcional)',
          ),
          maxLines: 3,
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('Cancelar'),
          ),
          ElevatedButton(
            onPressed: () => Navigator.pop(context, ctrl.text),
            child: const Text('Confirmar'),
          ),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final color = AppTheme.statusColor(apt.status);

    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(18),
        border: Border.all(color: const Color(0xFFF3F4F6)),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.03),
            blurRadius: 8,
            offset: const Offset(0, 2),
          ),
        ],
      ),
      child: Column(
        children: [
          // ── Header ────────────────────────────────────────────────────
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
            decoration: BoxDecoration(
              color: color.withOpacity(0.06),
              borderRadius:
                  const BorderRadius.vertical(top: Radius.circular(18)),
            ),
            child: Row(
              children: [
                Container(
                  padding: const EdgeInsets.all(8),
                  decoration: BoxDecoration(
                    color: color.withOpacity(0.15),
                    borderRadius: BorderRadius.circular(10),
                  ),
                  child: Icon(Icons.calendar_today_rounded,
                      color: color, size: 16),
                ),
                const SizedBox(width: 10),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        '${apt.appointmentDate ?? "-"} a las ${apt.appointmentTime ?? "-"}',
                        style: const TextStyle(
                          fontWeight: FontWeight.w600,
                          fontSize: 14,
                          color: Color(0xFF111827),
                        ),
                      ),
                      if (apt.serviceName != null)
                        Text(
                          apt.serviceName!,
                          style: const TextStyle(
                              fontSize: 12, color: Color(0xFF6B7280)),
                        ),
                    ],
                  ),
                ),
                StatusBadge(status: apt.status),
              ],
            ),
          ),
          // ── Body ──────────────────────────────────────────────────────
          Padding(
            padding: const EdgeInsets.all(16),
            child: Column(
              children: [
                _InfoRow(
                  icon: Icons.person_rounded,
                  label: apt.customerName,
                ),
                const SizedBox(height: 8),
                _InfoRow(
                  icon: Icons.phone_rounded,
                  label: apt.fullPhone,
                  onTap: () => callPhone(apt.fullPhone),
                ),
                if (apt.customerAddress != null &&
                    apt.customerAddress!.isNotEmpty) ...[
                  const SizedBox(height: 8),
                  _InfoRow(
                    icon: Icons.location_on_rounded,
                    label: apt.customerAddress!,
                  ),
                ],
                if (apt.notes != null && apt.notes!.isNotEmpty) ...[
                  const SizedBox(height: 8),
                  _InfoRow(
                    icon: Icons.notes_rounded,
                    label: apt.notes!,
                  ),
                ],
                // ── Actions ──────────────────────────────────────────────
                if (apt.status == 'pending' || apt.status == 'confirmed') ...[
                  const Divider(height: 24),
                  Wrap(
                    spacing: 8,
                    runSpacing: 8,
                    children: [
                      if (apt.status == 'pending')
                        _ActionButton(
                          label: 'Confirmar',
                          icon: Icons.check_circle_outline_rounded,
                          color: AppTheme.info,
                          onTap: () => _action(context, 'confirm'),
                        ),
                      if (apt.status != 'completed')
                        _ActionButton(
                          label: 'Completar',
                          icon: Icons.done_all_rounded,
                          color: AppTheme.success,
                          onTap: () => _action(context, 'complete'),
                        ),
                      _ActionButton(
                        label: 'No asistió',
                        icon: Icons.person_off_outlined,
                        color: AppTheme.warning,
                        onTap: () => _action(context, 'no-show'),
                      ),
                      _ActionButton(
                        label: 'Cancelar',
                        icon: Icons.cancel_outlined,
                        color: AppTheme.danger,
                        onTap: () => _action(context, 'cancel'),
                      ),
                    ],
                  ),
                ],
                // ── Quick Contact ─────────────────────────────────────────
                const Divider(height: 24),
                Row(
                  children: [
                    Expanded(
                      child: OutlinedButton.icon(
                        onPressed: () => callPhone(apt.fullPhone),
                        icon: const Icon(Icons.call_rounded, size: 16),
                        label: const Text('Llamar'),
                      ),
                    ),
                    const SizedBox(width: 10),
                    Expanded(
                      child: OutlinedButton.icon(
                        onPressed: () => openWhatsApp(
                          apt.fullPhone,
                          message:
                              'Hola ${apt.customerName}, te contacto sobre tu cita del ${apt.appointmentDate}.',
                        ),
                        icon: const Icon(Icons.chat_rounded, size: 16),
                        label: const Text('WhatsApp'),
                        style: OutlinedButton.styleFrom(
                            foregroundColor: const Color(0xFF25D366)),
                      ),
                    ),
                  ],
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class _InfoRow extends StatelessWidget {
  final IconData icon;
  final String label;
  final VoidCallback? onTap;

  const _InfoRow({required this.icon, required this.label, this.onTap});

  @override
  Widget build(BuildContext context) {
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(8),
      child: Row(
        children: [
          Icon(icon, size: 16, color: const Color(0xFF9CA3AF)),
          const SizedBox(width: 10),
          Expanded(
            child: Text(
              label,
              style: TextStyle(
                fontSize: 14,
                color: onTap != null ? AppTheme.primary : const Color(0xFF374151),
                decoration: onTap != null ? TextDecoration.underline : null,
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _ActionButton extends StatelessWidget {
  final String label;
  final IconData icon;
  final Color color;
  final VoidCallback onTap;

  const _ActionButton({
    required this.label,
    required this.icon,
    required this.color,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(10),
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 7),
        decoration: BoxDecoration(
          color: color.withOpacity(0.1),
          borderRadius: BorderRadius.circular(10),
          border: Border.all(color: color.withOpacity(0.3)),
        ),
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(icon, size: 14, color: color),
            const SizedBox(width: 5),
            Text(
              label,
              style: TextStyle(
                fontSize: 12,
                color: color,
                fontWeight: FontWeight.w600,
              ),
            ),
          ],
        ),
      ),
    );
  }
}
