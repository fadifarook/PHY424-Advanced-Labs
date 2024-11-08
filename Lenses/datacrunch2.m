function out = datacrunch2(infile,outfile,m_standard,o_offset,i_offset,l_offset);
%
%datacrunch2(infile, outfile, grid_size, o_off, i_off, l_off)
%
% takes a input file of the format
%   o_position i_position l_position grid_image_size
% and converts it to a file of the format
%   p dp q dq m dm
%   where p=corrected image-lens distance
%         q=corrected object-lens distance
%         m=magnification
%     and {dp, dq, dm} are uncertainties
%
% *blank lines delineate each set of measurements
% *each uncertainty is the STANDARD DEVIATION of the various points measured.
%
%
% example:
%  datacrunch('infile','myoutfile', 11.2)
% will take make a 'myoutfile' assuming an 11.2 mm grid size and no offsets.
%
% Note: data points measured only once will be given an uncertainty
% = twice the mean of the uncertainties calculated for the rest of the points.
%
%[Last revision: 28 March 2006]
%

outstring = '';
lasterr('');
SMALL = 1e-6;

global txtdata;

if nargin < 6; l_offset=0.0; end;
if nargin < 5; i_offset=0.0; end;
if nargin < 4; o_offset=0.0; end;
if nargin < 3; m_standard=10.0; end; %10mm

outstring=[outstring, sprintf('offsets:\t%.3f  object offset\n\t\t%.3f  image offset\n\t\t%.3f  lens offset\n', ...
    o_offset,  i_offset, l_offset)];

% load in data:
txtdata = textread(infile,'%s','delimiter','\n','whitespace','');
if ~isempty(lasterr),
    error(['Problem with ' infile]);
end;

line=1; numpoints=0;
data=[]; mdata=[]; o=[];do=[];i=[];di=[];l=[];dl=[];m=[];dm=[]; lengths=[]; lengthsm=[];
while (line <= length(txtdata))
    datachunk = sscanf(char(txtdata(line)),'%lf%lf%lf%lf', [4, 1]);
    if ~isempty(datachunk)
        data = [data datachunk(1:3)];
        if (length(datachunk)==4)
            mdata = [mdata datachunk(4)];
            numpoints = numpoints + 1;
        end
    elseif(length(data) > 0) %avg what we have so far
        lengths=[lengths length(data)];
        o = [ o mean(data(1,:)) + o_offset(1)];
        do = [ do std(data(1,:))/sqrt(length(data)) ];
        i = [ i mean(data(2,:)) + i_offset(1)];
        di = [ di std(data(2,:))/sqrt(length(data)) ];
        l = [ l mean(data(3,:)) + l_offset(1)];
        dl = [ dl std(data(3,:))/sqrt(length(data)) ];
        if (length(mdata) > 0)
            lengthsm=[lengthsm length(mdata)];
            m = [m mean(mdata)/m_standard(1)];
            dm = [dm m(end)*(std(mdata)/sqrt(length(mdata))/mean(mdata))];
        else
            m = [m 0]; dm = [dm 0];
        end
        data=[]; mdata=[];
    end
    line = line+1;
end
if (length(data)>0) %didn't finish up the last data point
    lengths=[lengths length(data)];
    o = [ o mean(data(1,:)) + o_offset(1)];
    do = [ do std(data(1,:))/sqrt(length(data)) ];
    i = [ i mean(data(2,:)) + i_offset(1)];
    di = [ di std(data(2,:))/sqrt(length(data)) ];
    l = [ l mean(data(3,:)) + l_offset(1)];
    dl = [ dl std(data(3,:))/sqrt(length(data)) ];
    if (length(mdata) > 0)
        lengthsm=[lengthsm length(mdata)];
        m = [m mean(mdata)/m_standard(1)];
        dm = [dm m(end)*(std(mdata)/sqrt(length(mdata))/mean(mdata))];
    else
        m = [m 0]; dm = [dm 0];
    end
end;

outstring=[outstring, sprintf('%s: %d points; %d sets loaded.\n',infile, numpoints,length(o))];

q = abs(o-l);
dq = sqrt(do.^2 + dl.^2);
p = abs(l-i);
dp = sqrt(dl.^2 + di.^2);
m = -abs(m); %note that m<0 for a single lens

%make sure there are no problematic zero uncertainties in q or m:
%replace quantities for which there is no uncertainty with an estimated
% standard deviation.

if (sum(dq < SMALL) > 0)
    zlist = find(dq(:)<SMALL)
    alist = find(dq(:)>SMALL)
    for j = 1:length(zlist)
        dq(zlist(j)) = sqrt(mean(lengths))*mean(dq(alist));
    end
    outstring=[outstring, sprintf('%d zero errors replaced in q.\n',length(zlist))];
end;
if (sum(dm < SMALL) > 0)
    zlist = find((dm(:)<SMALL)&(m(:)>0));
    alist = find(dm(:)>SMALL);
    for j = 1:length(zlist)
        dm(zlist(j)) = sqrt(mean(lengthsm))*mean(dm(alist));
    end
    outstring=[outstring, sprintf('%d zero errors replaced in m.\n',length(zlist))];
end;

%function output
out = [p; dp; q; dq; m; dm]';
%text messages
if (length(outstring)>0); disp(outstring); end;

%write out the file
fpout = fopen(outfile, 'w');
if ~isempty(lasterr),
    error([outfile ' n''est pas dans le repertoire en cours']);
end;
data = fprintf(fpout,'%8.4f %8.4f %8.4f %8.4f %8.4f %8.4f\n', ...
    out');
fclose(fpout);
