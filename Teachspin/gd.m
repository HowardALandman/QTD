% Do gradient descent optimization to fit muon lifetime,
% initial number of muons, and a uniform background noise
% to data from a Teachspin experiment.
% AUTHOR: Howard A. Landman, Oct 2012
%
% This was written and tested in Octave, but uses only basic
% features, and should be compatible with Matlab as well.

% Load Teachspin data as preprocessed by teachspin.perl.
fprintf('loading data.txt ...');
Y = load('data.txt');	% Should contain 997 bin counts,
bins = length(Y);	% but we don't hard-code that anywhere.
decays = sum(Y);	% total (true and false) decay events
fprintf('done, %d decays in %d bins\n',decays,bins);

% Set up for gradient descent.
b = 20; 	% nS, bin size
alpha = 0.0009;	% gradient descent rate-of-change factor
		% lower is slower but higher may not converge
num_iters = 10000000;

% initial guesses for tau, nu, and n, all floating point
tau = 2000.0; % nS
END_Y = Y((bins-99):bins); % estimate noise from last 100 bins
s = sum(END_Y);
nu = 0.0 + s / 100.0;	% expected number of decays in each bin
			% nu*bins = est. number of false decays
n = 0.0 + decays - nu*bins;	% est. number of real decays

K = 0:(bins-1);	% row vector 0 to 996
K = K'; 	% column vector 0 to 996

% Hypothesis -
% what we predict for each bin, based on tau nu and n.
% Note that this is a vector (one number per bin).
p = 1 - exp(-b/tau);	% prob. that a muon decays in 1 bin time
H = zeros(size(K));
H = nu + n*p*((1-p) .^ K);

% error
D = H - Y;
E = D .^ 2;
v = sum(E);
fprintf('Initial settings\n');
fprintf('n=%f, tau=%f, nu=%f, v=%f\n',n,tau,nu,v);

% Begin main loop.
for iter = 1:num_iters
%fprintf('iter=%d\n',iter);

% We could solve for nu exactly with this code,
% since its gradient has a particularly simple form,
% but choose instead to treat it the same as tau and n.
%fprintf('Solve for best nu\n');
%delta_nu = sum(D) / bins;
%nu = nu + delta_nu ;
% Update hypothesis and recalculate error
%H = nu + n*p*((1-p) .^ K);
%D = H - Y;
%E = D .^ 2;
%v = sum(E);
%fprintf('nu: iter=%d, n=%f, tau=%f, nu=%f, v=%f\n',
%	iter,n,tau,nu,v);

% Calculate one step of gradient descent for nu, n and tau.
% See the discussion in the main paper for derivations.

% dV/dnu
dvdnu = 2*sum(D); % This points UPHILL but we want to go DOWNHILL
delta_nu = -alpha*dvdnu; % hence the minus sign here.

% Cross-check dV/dnu calculation (for debugging).
%Hplus = (nu + 0.001) + n*p*((1-p) .^ K);
%Hminus = (nu - 0.001) + n*p*((1-p) .^ K);
%Dplus = Hplus - Y;
%Dminus = Hminus - Y;
%Eplus = Dplus .^ 2;
%Eminus = Dminus .^ 2;
%Vplus = sum(Eplus);
%Vminus = sum(Eminus);
%dvdnu_est = (Vplus - Vminus) / 0.002
%fprintf('dvdnu=%f, dvdnu_est=%f\n',dvdnu,dvdnu_est);

% dV/dn
DN = D .* ((1-p) .^ K);
dvdn = 2*p*sum(DN);
delta_n = -alpha*dvdn;

% Cross-check dV/dn calculation (for debugging).
%Hplus = nu + (n + 0.001)*p*((1-p) .^ K);
%Hminus = nu + (n - 0.001)*p*((1-p) .^ K);
%Dplus = Hplus - Y;
%Dminus = Hminus - Y;
%Eplus = Dplus .^ 2;
%Eminus = Dminus .^ 2;
%Vplus = sum(Eplus);
%Vminus = sum(Eminus);
%dvdn_est = (Vplus - Vminus) / 0.002
%fprintf('dvdn=%f, dvdn_est=%f\n',dvdn,dvdn_est);

% dV/dtau
PK = (1-p) .^ K;
DTAU = D .* ((PK .* (1-p)) - p*(K .* PK));
dvdtau = (-2*n*b / (tau*tau)) * sum(DTAU);
delta_tau = -alpha*dvdtau;

% Cross-check dV/dtau calculation (for debugging).
%pplus = 1 - exp(-b/(tau+0.001));
%pminus = 1 - exp(-b/(tau-0.001));
%Hplus = nu + n*pplus*((1-pplus) .^ K);
%Hminus = nu + n*pminus*((1-pminus) .^ K);
%Dplus = Hplus - Y;
%Dminus = Hminus - Y;
%Eplus = Dplus .^ 2;
%Eminus = Dminus .^ 2;
%Vplus = sum(Eplus);
%Vminus = sum(Eminus);
%dvdtau_est = (Vplus - Vminus) / 0.002;
%fprintf('dvdtau=%f, dvdtau_est=%f\n',dvdtau,dvdtau_est);

% Update simultaneously.
nu = nu + delta_nu;
n = n + delta_n;
tau = tau + delta_tau;

v_old = v;
% Update hypothesis and recalculate error
p = 1 - exp(-b/tau);
H = nu + n*p*((1-p) .^ K);
D = H - Y;
E = D .^ 2;
v = sum(E);
v_diff = v - v_old;

% For iteration-by-iteration statistics, just move the
% following fprintf statement inside the loop here.
% With 10 million iterations, this is too verbose.

end

% Print final results
fprintf('iter=%d, n=%f, tau=%f (p=%f), nu=%f, v=%f, delta=%f\n',
	iter,n,tau,p,nu,v,v_diff);
