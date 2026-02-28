import 'dart:async';
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../../core/theme/app_theme.dart';
import '../../../core/utils/helpers.dart';
import '../../../data/providers/app_provider.dart';
import '../../../data/providers/auth_provider.dart';
import '../../../data/models/models.dart';
import '../../widgets/common/widgets.dart';

class TicketsScreen extends StatefulWidget {
  const TicketsScreen({super.key});

  @override
  State<TicketsScreen> createState() => _TicketsScreenState();
}

class _TicketsScreenState extends State<TicketsScreen> {
  Timer? _autoRefresh;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      _load();
    });
    // Auto-refresh cada 15 segundos
    _autoRefresh = Timer.periodic(const Duration(seconds: 15), (_) => _load());
  }

  @override
  void dispose() {
    _autoRefresh?.cancel();
    super.dispose();
  }

  void _load() => context.read<AppProvider>().fetchTickets();

  @override
  Widget build(BuildContext context) {
    final provider = context.watch<AppProvider>();
    final user = context.watch<AuthProvider>().user;

    // Si el usuario no tiene sistema de turnos
    if (!(user?.hasTicketSystem ?? false)) {
      return Scaffold(
        appBar: AppBar(title: const Text('Sistema de Turnos')),
        body: const EmptyState(
          icon: Icons.queue_outlined,
          title: 'Sin sistema de turnos',
          subtitle:
              'El sistema de turnos debe ser activado por un administrador.',
        ),
      );
    }

    final data = provider.ticketsData;

    if (provider.loadingTickets && data == null) {
      return Scaffold(
        appBar: AppBar(title: const Text('Sistema de Turnos')),
        body: const ShimmerList(count: 5),
      );
    }

    final enabled = data?['enabled'] ?? false;
    final isAccepting = data?['is_accepting'] ?? true;
    final businessName = data?['business_name'] ?? 'Consultorio';
    final stats = data?['stats'] as Map<String, dynamic>? ?? {};
    final currentTicket = data?['current_ticket'] != null
        ? TicketModel.fromJson(data!['current_ticket'])
        : null;
    final waitingTickets = (data?['tickets'] as List? ?? [])
        .map((t) => TicketModel.fromJson(t))
        .where((t) => t.status == 'waiting')
        .toList();

    return Scaffold(
      appBar: AppBar(
        title: Text(businessName),
        actions: [
          // Toggle accepting tickets
          IconButton(
            onPressed: () async {
              final ok = await context.read<AppProvider>().toggleAccepting();
              if (!context.mounted) return;
              showSnack(
                context,
                ok
                    ? (isAccepting
                        ? 'Turnos pausados'
                        : 'Turnos reanudados')
                    : 'Error al cambiar estado',
                isError: !ok,
              );
            },
            icon: Icon(
              isAccepting
                  ? Icons.pause_circle_outline_rounded
                  : Icons.play_circle_outline_rounded,
              color: isAccepting ? AppTheme.warning : AppTheme.success,
            ),
            tooltip: isAccepting ? 'Pausar turnos' : 'Reanudar turnos',
          ),
          IconButton(
            onPressed: _load,
            icon: const Icon(Icons.refresh_rounded),
          ),
        ],
      ),
      body: !enabled
          ? const EmptyState(
              icon: Icons.do_not_disturb_alt_outlined,
              title: 'Sistema desactivado',
              subtitle: 'Contacta al administrador para activar el sistema.',
            )
          : RefreshIndicator(
              onRefresh: () async => _load(),
              child: CustomScrollView(
                slivers: [
                  // ── Status Banner ───────────────────────────────────────
                  SliverToBoxAdapter(
                    child: _StatusBanner(isAccepting: isAccepting),
                  ),

                  // ── Stats ───────────────────────────────────────────────
                  SliverPadding(
                    padding: const EdgeInsets.fromLTRB(16, 8, 16, 8),
                    sliver: SliverGrid(
                      gridDelegate:
                          const SliverGridDelegateWithFixedCrossAxisCount(
                        crossAxisCount: 4,
                        crossAxisSpacing: 8,
                        mainAxisSpacing: 8,
                        childAspectRatio: 0.85,
                      ),
                      delegate: SliverChildListDelegate([
                        _StatMini(
                          label: 'En espera',
                          value: '${stats['waiting'] ?? 0}',
                          color: AppTheme.warning,
                        ),
                        _StatMini(
                          label: 'Atendidos',
                          value: '${stats['completed'] ?? 0}',
                          color: AppTheme.success,
                        ),
                        _StatMini(
                          label: 'Cancelados',
                          value: '${stats['cancelled'] ?? 0}',
                          color: AppTheme.danger,
                        ),
                        _StatMini(
                          label: 'No asistió',
                          value: '${stats['no_show'] ?? 0}',
                          color: const Color(0xFF6B7280),
                        ),
                      ]),
                    ),
                  ),

                  // ── Current Ticket ──────────────────────────────────────
                  if (currentTicket != null)
                    SliverToBoxAdapter(
                      child: Padding(
                        padding: const EdgeInsets.fromLTRB(16, 8, 16, 0),
                        child: _CurrentTicketCard(ticket: currentTicket),
                      ),
                    ),

                  // ── Call Next Button ────────────────────────────────────
                  SliverToBoxAdapter(
                    child: Padding(
                      padding: const EdgeInsets.all(16),
                      child: _CallNextButton(hasWaiting: waitingTickets.isNotEmpty),
                    ),
                  ),

                  // ── Waiting Queue ───────────────────────────────────────
                  if (waitingTickets.isNotEmpty) ...[
                    SliverToBoxAdapter(
                      child: SectionHeader(
                        title: 'En espera (${waitingTickets.length})',
                      ),
                    ),
                    SliverPadding(
                      padding: const EdgeInsets.symmetric(horizontal: 16),
                      sliver: SliverList(
                        delegate: SliverChildBuilderDelegate(
                          (_, i) => _TicketTile(
                            ticket: waitingTickets[i],
                            position: i + 1,
                          ),
                          childCount: waitingTickets.length,
                        ),
                      ),
                    ),
                  ] else
                    const SliverToBoxAdapter(
                      child: EmptyState(
                        icon: Icons.check_circle_outline_rounded,
                        title: 'Sin turnos en espera',
                        subtitle: 'La sala está vacía por el momento.',
                      ),
                    ),

                  const SliverToBoxAdapter(child: SizedBox(height: 32)),
                ],
              ),
            ),
    );
  }
}

class _StatusBanner extends StatelessWidget {
  final bool isAccepting;
  const _StatusBanner({required this.isAccepting});

  @override
  Widget build(BuildContext context) {
    return Container(
      margin: const EdgeInsets.all(16),
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: isAccepting
            ? AppTheme.success.withOpacity(0.1)
            : AppTheme.warning.withOpacity(0.1),
        borderRadius: BorderRadius.circular(14),
        border: Border.all(
          color: isAccepting
              ? AppTheme.success.withOpacity(0.3)
              : AppTheme.warning.withOpacity(0.3),
        ),
      ),
      child: Row(
        children: [
          Icon(
            isAccepting ? Icons.check_circle_rounded : Icons.pause_circle_rounded,
            color: isAccepting ? AppTheme.success : AppTheme.warning,
          ),
          const SizedBox(width: 10),
          Text(
            isAccepting ? 'Aceptando turnos' : 'Turnos pausados',
            style: TextStyle(
              fontWeight: FontWeight.w600,
              color: isAccepting ? AppTheme.success : AppTheme.warning,
            ),
          ),
        ],
      ),
    );
  }
}

class _CurrentTicketCard extends StatelessWidget {
  final TicketModel ticket;
  const _CurrentTicketCard({required this.ticket});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        gradient: const LinearGradient(
          colors: [AppTheme.primary, AppTheme.secondary],
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
        ),
        borderRadius: BorderRadius.circular(20),
        boxShadow: [
          BoxShadow(
            color: AppTheme.primary.withOpacity(0.3),
            blurRadius: 16,
            offset: const Offset(0, 6),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text(
            'TURNO ACTUAL',
            style: TextStyle(
              color: Colors.white70,
              fontSize: 11,
              fontWeight: FontWeight.w600,
              letterSpacing: 1.2,
            ),
          ),
          const SizedBox(height: 8),
          Row(
            crossAxisAlignment: CrossAxisAlignment.end,
            children: [
              Text(
                ticket.ticketNumber,
                style: const TextStyle(
                  color: Colors.white,
                  fontSize: 52,
                  fontWeight: FontWeight.w800,
                  letterSpacing: -1,
                ),
              ),
              const SizedBox(width: 16),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      ticket.patientName,
                      style: const TextStyle(
                        color: Colors.white,
                        fontSize: 16,
                        fontWeight: FontWeight.w600,
                      ),
                    ),
                    if (ticket.ticketTypeName != null)
                      Text(
                        ticket.ticketTypeName!,
                        style: const TextStyle(
                            color: Colors.white70, fontSize: 13),
                      ),
                  ],
                ),
              ),
            ],
          ),
          const SizedBox(height: 16),
          Row(
            children: [
              Expanded(
                child: _TicketAction(
                  label: 'Completar',
                  icon: Icons.done_all_rounded,
                  onTap: () async {
                    final ok = await context
                        .read<AppProvider>()
                        .updateTicketStatus(ticket.id, 'complete');
                    if (context.mounted) {
                      showSnack(context, ok ? 'Turno completado' : 'Error',
                          isError: !ok);
                    }
                  },
                ),
              ),
              const SizedBox(width: 10),
              Expanded(
                child: _TicketAction(
                  label: 'No asistió',
                  icon: Icons.person_off_outlined,
                  onTap: () async {
                    final ok = await context
                        .read<AppProvider>()
                        .updateTicketStatus(ticket.id, 'no-show');
                    if (context.mounted) {
                      showSnack(context, ok ? 'Marcado como ausente' : 'Error',
                          isError: !ok);
                    }
                  },
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }
}

class _TicketAction extends StatelessWidget {
  final String label;
  final IconData icon;
  final VoidCallback onTap;
  const _TicketAction(
      {required this.label, required this.icon, required this.onTap});

  @override
  Widget build(BuildContext context) {
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(12),
      child: Container(
        padding: const EdgeInsets.symmetric(vertical: 10),
        decoration: BoxDecoration(
          color: Colors.white.withOpacity(0.2),
          borderRadius: BorderRadius.circular(12),
          border: Border.all(color: Colors.white.withOpacity(0.3)),
        ),
        child: Row(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(icon, color: Colors.white, size: 16),
            const SizedBox(width: 6),
            Text(
              label,
              style: const TextStyle(
                color: Colors.white,
                fontWeight: FontWeight.w600,
                fontSize: 13,
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _CallNextButton extends StatefulWidget {
  final bool hasWaiting;
  const _CallNextButton({required this.hasWaiting});

  @override
  State<_CallNextButton> createState() => _CallNextButtonState();
}

class _CallNextButtonState extends State<_CallNextButton> {
  bool _calling = false;

  Future<void> _callNext() async {
    setState(() => _calling = true);
    final result = await context.read<AppProvider>().callNextTicket();
    setState(() => _calling = false);
    if (!mounted) return;

    final ticket = result?['ticket'];
    if (ticket != null) {
      final t = TicketModel.fromJson(ticket);
      showSnack(context, 'Llamando turno ${t.ticketNumber} - ${t.patientName}');
    } else {
      showSnack(context, 'No hay turnos en espera', isError: true);
    }
  }

  @override
  Widget build(BuildContext context) {
    return GradientButton(
      label: 'Llamar siguiente turno',
      icon: Icons.campaign_rounded,
      loading: _calling,
      onPressed: widget.hasWaiting ? _callNext : null,
    );
  }
}

class _StatMini extends StatelessWidget {
  final String label;
  final String value;
  final Color color;

  const _StatMini(
      {required this.label, required this.value, required this.color});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(10),
      decoration: BoxDecoration(
        color: color.withOpacity(0.1),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: color.withOpacity(0.2)),
      ),
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Text(
            value,
            style: TextStyle(
              fontSize: 22,
              fontWeight: FontWeight.w800,
              color: color,
            ),
          ),
          const SizedBox(height: 2),
          Text(
            label,
            textAlign: TextAlign.center,
            style: TextStyle(
              fontSize: 9,
              color: color.withOpacity(0.8),
              fontWeight: FontWeight.w600,
            ),
          ),
        ],
      ),
    );
  }
}

class _TicketTile extends StatelessWidget {
  final TicketModel ticket;
  final int position;
  const _TicketTile({required this.ticket, required this.position});

  @override
  Widget build(BuildContext context) {
    final typeColor = ticket.ticketTypeColor != null
        ? _hexColor(ticket.ticketTypeColor!)
        : AppTheme.primary;

    return Container(
      margin: const EdgeInsets.only(bottom: 8),
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: const Color(0xFFF3F4F6)),
      ),
      child: Row(
        children: [
          // Position
          Container(
            width: 36,
            height: 36,
            decoration: BoxDecoration(
              color: typeColor.withOpacity(0.1),
              borderRadius: BorderRadius.circular(10),
            ),
            child: Center(
              child: Text(
                '$position',
                style: TextStyle(
                  color: typeColor,
                  fontWeight: FontWeight.w700,
                  fontSize: 16,
                ),
              ),
            ),
          ),
          const SizedBox(width: 12),
          // Ticket number
          Text(
            ticket.ticketNumber,
            style: TextStyle(
              fontSize: 20,
              fontWeight: FontWeight.w800,
              color: typeColor,
            ),
          ),
          const SizedBox(width: 12),
          // Name & type
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  ticket.patientName,
                  style: const TextStyle(
                    fontWeight: FontWeight.w600,
                    fontSize: 14,
                    color: Color(0xFF111827),
                  ),
                ),
                if (ticket.ticketTypeName != null)
                  Text(
                    ticket.ticketTypeName!,
                    style: const TextStyle(
                        fontSize: 12, color: Color(0xFF9CA3AF)),
                  ),
              ],
            ),
          ),
          // Priority badge
          if (ticket.isPriority)
            Container(
              padding:
                  const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
              decoration: BoxDecoration(
                color: AppTheme.accent.withOpacity(0.1),
                borderRadius: BorderRadius.circular(20),
              ),
              child: const Text(
                'Prioridad',
                style: TextStyle(
                  fontSize: 10,
                  color: AppTheme.accent,
                  fontWeight: FontWeight.w600,
                ),
              ),
            ),
        ],
      ),
    );
  }

  Color _hexColor(String hex) {
    try {
      final h = hex.replaceAll('#', '');
      return Color(int.parse('FF$h', radix: 16));
    } catch (_) {
      return AppTheme.primary;
    }
  }
}
